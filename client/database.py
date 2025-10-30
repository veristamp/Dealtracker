import datetime
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List

from sqlalchemy import (Boolean, Column, DateTime, Float, Integer,
                        String, create_engine, JSON)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)

# --- Database Setup ---
APP_DATA_DIR = Path.home() / ".dealtracker_secure"
APP_DATA_DIR.mkdir(exist_ok=True)
DATABASE_URL = f"sqlite:///{APP_DATA_DIR / 'dealtracker_client.db'}"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_aware_utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


# --- Database Models ---
class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, index=True, nullable=False)
    product_name = Column(String)
    scraped_price = Column(Float, nullable=False)
    threshold_price = Column(Float, nullable=False)
    currency = Column(String(3), default="INR")
    timestamp = Column(DateTime(timezone=True), default=get_aware_utc_now, index=True)

    def to_dict(self):
        data = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        if isinstance(data.get('timestamp'), datetime.datetime):
            data['timestamp'] = data['timestamp'].strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        return data

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=get_aware_utc_now, index=True)
    action_type = Column(String, nullable=False)
    details = Column(JSON, nullable=True)

    def to_dict(self):
        data = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        if isinstance(data.get('timestamp'), datetime.datetime):
            data['timestamp'] = data['timestamp'].strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        return data

class PriceHistory(Base):
    __tablename__ = "price_history"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=get_aware_utc_now, index=True)
    price = Column(Float, nullable=False)

    def to_dict(self):
        data = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        if isinstance(data.get('timestamp'), datetime.datetime):
            data['timestamp'] = data['timestamp'].strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        return data

class ProductCache(Base):
    __tablename__ = "product_cache"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, unique=True, index=True)
    url = Column(String, nullable=False)
    name = Column(String)
    current_price = Column(Float)
    threshold_price = Column(Float)
    timestamp = Column(DateTime(timezone=True), default=get_aware_utc_now, index=True)
    active = Column(Boolean, default=True, index=True)
    last_scrape_status = Column(String, default="pending")
    tag = Column(String, nullable=True)

    def to_dict(self):
        data = {c.name: getattr(self, c.name) for c in self.__table__.columns}

        if isinstance(data.get('timestamp'), datetime.datetime): 
            data['timestamp'] = data['timestamp'].strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        return data

class AppSettings(Base):
    __tablename__ = "app_settings"
    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)

# --- Database Manager ---
class DatabaseManager:
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
        self._initialize_database()

    def _initialize_database(self):
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database initialized successfully.")

    @contextmanager
    def get_session(self):
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
        finally:
            session.close()

    def get_cached_products(self, active_only: bool = False) -> List[Dict[str, Any]]:
        with self.get_session() as session:
            query = session.query(ProductCache).order_by(ProductCache.id.desc())
            if active_only:
                query = query.filter(ProductCache.active == True)
            return [p.to_dict() for p in query.all()]

    def add_activity_log(self, action_type: str, details: Dict = None):
        with self.get_session() as session:
            log_entry = ActivityLog(action_type=action_type, details=details or {})
            session.add(log_entry)
        logger.info(f"Activity logged: {action_type} - {details}")

    def get_activity_logs(self, limit: int = 50) -> List[Dict]:
        with self.get_session() as session:
            logs = session.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(limit).all()
            return [log.to_dict() for log in logs]

    def add_price_history_entry(self, product_id: int, price: float):
        with self.get_session() as session:
            history_entry = PriceHistory(product_id=product_id, price=price)
            session.add(history_entry)

    def get_price_history_for_product(self, product_id: int, limit: int = 100) -> List[Dict]:
        with self.get_session() as session:
            history = session.query(PriceHistory).filter_by(product_id=product_id).order_by(PriceHistory.timestamp.asc()).limit(limit).all()
            return [entry.to_dict() for entry in history]

    def cache_product(self, product_data: dict):
        with self.get_session() as session:
            entry = session.query(ProductCache).filter(ProductCache.product_id == product_data['id']).first()
            if entry:
                is_active_local = entry.active
                local_tag = entry.tag
                entry.url = product_data.get('url')
                entry.name = product_data.get('name')
                entry.threshold_price = product_data.get('price_threshold')
                entry.timestamp = datetime.datetime.now(datetime.timezone.utc)
                entry.active = is_active_local
                entry.tag = local_tag
            else:
                tag = "myntra" if "myntra.com" in product_data.get('url', '') else "flipkart"
                new_entry = ProductCache(
                    product_id=product_data.get('id'),
                    url=product_data.get('url'),
                    name=product_data.get('name', 'Unknown Product'),
                    threshold_price=product_data.get('price_threshold', 0),
                    active=True,
                    tag=tag
                )
                session.add(new_entry)

    def update_product_details(self, product_id: int, details: Dict[str, Any]):
        with self.get_session() as session:
            product = session.query(ProductCache).filter(ProductCache.product_id == product_id).first()
            if product:
                for key, value in details.items():
                    if hasattr(product, key):
                        setattr(product, key, value)
                product.timestamp = datetime.datetime.now(datetime.timezone.utc)

    def save_setting(self, key: str, value: str):
        with self.get_session() as session:
            setting = session.query(AppSettings).filter_by(key=key).first()
            if setting:
                setting.value = value
            else:
                setting = AppSettings(key=key, value=value)
                session.add(setting)
            logger.info(f"Saved setting: {key} = {value}")

    def get_setting(self, key: str, default: str = None) -> str:
        with self.get_session() as session:
            setting = session.query(AppSettings).filter_by(key=key).first()
            return setting.value if setting else default

    def delete_products_by_id(self, product_ids: List[int]):
        if not product_ids:
            return
        with self.get_session() as session:
            session.query(ProductCache).filter(ProductCache.product_id.in_(product_ids)).delete(synchronize_session=False)
            logger.info(f"Deleted {len(product_ids)} stale products from local cache.")

    def add_alert(self, product_id: int, product_name: str, scraped_price: float, threshold_price: float):
        with self.get_session() as session:
            exists = session.query(Alert).filter_by(product_id=product_id, scraped_price=scraped_price).first()
            if not exists:
                alert = Alert(
                    product_id=product_id,
                    product_name=product_name,
                    scraped_price=scraped_price,
                    threshold_price=threshold_price,
                    currency="INR"
                )
                session.add(alert)
                logger.info(f"Alert created for '{product_name}' at ₹{scraped_price}")

    def get_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_session() as session:
            alerts = session.query(Alert).order_by(Alert.timestamp.desc()).limit(limit).all()
            return [a.to_dict() for a in alerts]

    def delete_alerts_for_product(self, product_id: int):
        try:
            with self.get_session() as session:
                session.query(Alert).filter(Alert.product_id == product_id).delete(synchronize_session=False)
            logging.info(f"Deleted all alerts for product_id: {product_id}")
        except Exception as e:
            logging.error(f"Failed to delete alerts for product {product_id}: {e}")
            

    def delete_product(self, product_id: int):
        try:
            with self.get_session() as session:
                session.query(ProductCache).filter(ProductCache.product_id == product_id).delete(synchronize_session=False)
            logging.info(f"Deleted product with id: {product_id}")
        except Exception as e:
            logging.error(f"Failed to delete product {product_id}: {e}")

    def clear_all_alerts(self):
        try:
            with self.get_session() as session:
                session.query(Alert).delete(synchronize_session=False)
            logging.info("Cleared all previous alerts from the local database.")
        except Exception as e:
            logging.error(f"Failed to clear alerts table: {e}")

    def get_dashboard_stats(self) -> Dict[str, int]:
        with self.get_session() as session:
            total_products = session.query(ProductCache).count()
            active_deals = session.query(Alert.product_id).distinct().count()
            return {"total_products": total_products, "active_deals": active_deals}