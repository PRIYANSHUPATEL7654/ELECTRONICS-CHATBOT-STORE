from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .models import Product

IMAGES = {
    "Phones": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=900&q=80",
    "Laptops": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=900&q=80",
    "Headphones": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=900&q=80",
    "Smartwatches": "https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=900&q=80",
    "Earbuds": "https://images.unsplash.com/photo-1606220945770-b5b6c2c55bf1?w=900&q=80",
    "Cameras": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=900&q=80",
    "Accessories": "https://images.unsplash.com/photo-1625842268584-8f3296236761?w=900&q=80",
}

PRODUCTS = [
("Nova X1 5G","Balanced 5G smartphone with AMOLED display, dependable cameras, and all-day battery.",28999,"Phones",24),
("Nova X1 Pro","Premium 5G phone with 120Hz display, fast charging, and a versatile triple camera.",44999,"Phones",16),
("PixelPeak A2","Clean Android experience, excellent computational photography, and compact design.",32999,"Phones",18),
("PixelPeak Ultra","Flagship camera phone with 6.7-inch OLED, wireless charging, and long-term updates.",79999,"Phones",9),
("Orion Note 12","Large-screen productivity phone with stylus, 256GB storage, and 5000mAh battery.",37999,"Phones",20),
("Orion Note 12 Lite","Affordable large-display phone with smooth performance, dual SIM, and quick charging.",21999,"Phones",31),
("Zenith Fold Mini","Pocket-friendly foldable phone with cover screen and strong multitasking performance.",89999,"Phones",5),
("Volt S20","Gaming-ready phone with high refresh rate, stereo speakers, and vapor chamber cooling.",26999,"Phones",14),
("AeroBook 14","Portable 14-inch laptop with Ryzen 7, 16GB RAM, and fast 512GB SSD.",64999,"Laptops",12),
("AeroBook 15 Creator","Color-accurate creator laptop with Core i7, 16GB RAM, and dedicated graphics.",94999,"Laptops",7),
("ThinkLite 14","Student laptop with Core i5, 8GB RAM, and comfortable backlit keyboard.",52999,"Laptops",22),
("ThinkLite 15","Value-focused 15.6-inch laptop for office work, browsing, coding, and study.",42999,"Laptops",28),
("CodeForge Pro","Developer laptop with 32GB RAM, 1TB SSD, high-resolution display, and excellent thermals.",124999,"Laptops",4),
("CodeForge Air","Slim coding companion with long battery life, metal body, and 16GB memory.",79999,"Laptops",10),
("GameCore 16","Performance gaming laptop with 165Hz display, RTX graphics, and upgraded cooling.",139999,"Laptops",6),
("GameCore 15","Mid-range gaming laptop with RTX graphics, 16GB RAM, and 144Hz panel.",89999,"Laptops",11),
("StudioBook OLED","Creator OLED laptop with wide color coverage and powerful H-series processor.",114999,"Laptops",5),
("TravelMate 13","Lightweight travel laptop with 12-hour battery, Wi-Fi 6E, and durable hinge.",69999,"Laptops",15),
("BassFlow 700","Wireless over-ear headphones with adaptive ANC, rich bass, and 40-hour battery.",8999,"Headphones",35),
("QuietSpace Max","Premium ANC headphones with spatial audio, multipoint Bluetooth, and plush cushions.",24999,"Headphones",13),
("StudioMonitor H1","Wired monitoring headphones with balanced sound and detachable cable.",6999,"Headphones",19),
("TravelBeats 2","Foldable wireless headphones for commutes with quick charging and clear calls.",4999,"Headphones",42),
("SoundArc 360","Immersive headphones with head tracking, EQ controls, and low-latency mode.",15999,"Headphones",17),
("Pulse Buds Pro","True wireless earbuds with ANC, wireless charging case, and IPX5 resistance.",7999,"Earbuds",29),
("Pulse Buds Lite","Affordable earbuds with comfortable fit, touch controls, and 24-hour battery.",2499,"Earbuds",60),
("AirLoop 3","Open-fit earbuds with spatial sound, transparency mode, and device switching.",14999,"Earbuds",18),
("ClearCall TWS","Call-first earbuds with four microphones, wind reduction, and pocket case.",3999,"Earbuds",38),
("RunnerPods Sport","Sport earbuds with ear hooks, IPX7 protection, and ten-hour battery.",5999,"Earbuds",25),
("TimeTrack S5","Fitness smartwatch with GPS, heart-rate tracking, sleep insights, and AMOLED screen.",11999,"Smartwatches",23),
("TimeTrack Active","Rugged sports watch with multi-band GPS, training metrics, and two-week battery.",24999,"Smartwatches",8),
("UrbanWatch 2","Everyday smartwatch with calling, notifications, NFC payments, and health tracking.",8999,"Smartwatches",26),
("KidsWatch Connect","Family smartwatch with location sharing, safe zones, SOS calling, and durable strap.",6999,"Smartwatches",21),
("FitBand Neo","Slim fitness band with step tracking, blood oxygen trends, and color display.",2999,"Smartwatches",44),
("Lumina Mirrorless M50","Compact mirrorless camera with 24MP sensor, 4K video, and fast autofocus.",58999,"Cameras",8),
("Lumina VlogCam","Pocket vlogging camera with flip screen, microphone input, and stabilized video.",34999,"Cameras",10),
("TrailShot Action 6","Rugged 4K action camera with horizon leveling, waterproof housing, and slow motion.",19999,"Cameras",16),
("ProLens 50 Prime","Bright 50mm prime lens with smooth bokeh and sharp portraits.",27999,"Cameras",5),
("SnapMini Gimbal","Three-axis smartphone gimbal with subject tracking and foldable arms.",8999,"Cameras",19),
("ChargeHub 65W","GaN USB-C charger with three ports, laptop support, and compact travel design.",3499,"Accessories",53),
("ChargeHub 100W","High-output GaN charger for laptops, tablets, and phones with power distribution.",5999,"Accessories",34),
("PowerBank Pro 20K","20000mAh power bank with 65W USB-C, display, and pass-through charging.",4999,"Accessories",27),
("PowerBank Slim 10K","Slim 10000mAh power bank with dual outputs and fast charging.",1999,"Accessories",48),
("KeyBoard MX Wireless","Low-profile multi-device keyboard with quiet keys and backlighting.",6999,"Accessories",22),
("ClickMaster Ergo","Ergonomic wireless mouse with silent clicks, adjustable DPI, and thumb rest.",2499,"Accessories",41),
("VisionDock 4K","USB-C dock with 4K HDMI, Ethernet, card reader, and 100W pass-through.",7999,"Accessories",14),
("ShieldGlass Pro","Tempered glass screen protector with anti-fingerprint coating and alignment tray.",999,"Accessories",75),
("DeskSound Mini","Compact USB-C desktop speaker with full sound and physical volume dial.",2999,"Accessories",30),
("StreamMic USB","USB condenser microphone for calls, podcasts, gaming, and online classes.",5499,"Accessories",18),
("Nova Edge 5G","Slim 5G phone with a bright 120Hz display, stereo speakers, and reliable cameras.",29999,"Phones",19),
("HomeHub Display","Compact smart display for timers, music, video calls, and connected-home controls.",6499,"Accessories",26),
]

def seed_products(db: Session) -> None:
    if (db.scalar(select(func.count(Product.id))) or 0) >= 50:
        return
    for name, description, price, category, stock in PRODUCTS:
        db.add(Product(name=name, description=description, price=price, category=category, stock=stock, image_url=IMAGES[category]))
    db.commit()
