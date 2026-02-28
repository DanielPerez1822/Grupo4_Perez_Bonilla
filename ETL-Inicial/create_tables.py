from scripts.database import engine
from scripts.models import Base

Base.metadata.create_all(bind=engine)

print("Tablas creadas correctamente")