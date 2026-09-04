import os
from PIL import Image, ImageDraw, ImageFont

def draw_chips_label(output_path: str):
    # Width 800, Height 1200 - Pouch proportion
    img = Image.new("RGB", (800, 1200), color=(235, 60, 30))
    draw = ImageDraw.Draw(img)

    # Header banner (Deep yellow/gold)
    draw.rectangle([(20, 20), (780, 180)], fill=(255, 195, 0), outline=(200, 150, 0), width=4)
    draw.text((220, 50), "DESI CRUNCH", fill=(180, 20, 10))
    draw.text((250, 110), "SNACK COMPANY", fill=(40, 40, 40))

    # Product Title
    draw.rectangle([(50, 220), (750, 320)], fill=(255, 255, 255), outline=(100, 10, 10), width=3)
    draw.text((120, 240), "CRUNCHY MAGIC MASALA", fill=(190, 20, 10))
    draw.text((270, 280), "POTATO CHIPS", fill=(30, 30, 30))

    # Graphics placeholder (Chips illustration)
    draw.ellipse([(250, 360), (550, 600)], fill=(255, 215, 0), outline=(220, 160, 0), width=6)
    draw.text((310, 470), "HOT & SPICY", fill=(180, 20, 10))

    # Mandatory Declarations White Panel (Back/Lower area)
    draw.rectangle([(60, 650), (740, 1160)], fill=(255, 255, 255), outline=(80, 80, 80), width=3)
    
    # Declarations content (exact matching our fixture bounding boxes)
    # y: 0.68 -> 816, x: 0.14 -> 112
    draw.text((110, 820), "Net Wt.: 120 gms", fill=(0, 0, 0))
    draw.text((450, 820), "Country of Origin: India", fill=(0, 0, 0))

    # y: 0.74 -> 888
    draw.text((110, 890), "MRP: ₹ 35.00", fill=(0, 0, 0))
    
    # y: 0.80 -> 960
    draw.text((110, 960), "Pkd: 06/2026   Batch: LOT-2026-B88", fill=(0, 0, 0))

    # y: 0.86 -> 1032
    draw.text((95, 1040), "Mfd. by: Desi Snacks Ltd., Plot 14, Phase II,", fill=(0, 0, 0))
    draw.text((95, 1070), "Industrial Area, Okhla, New Delhi - 110020", fill=(0, 0, 0))

    # y: 0.94 -> 1128
    draw.text((110, 1130), "Consumer Care: feedback@desisnacks.com", fill=(0, 0, 0))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, quality=92)
    print(f"Generated Chips Label: {output_path}")

def draw_coffee_label(output_path: str):
    # Elegant dark artisan coffee pouch (800x1200)
    img = Image.new("RGB", (800, 1200), color=(26, 20, 18))
    draw = ImageDraw.Draw(img)

    # Gold elegant frame
    draw.rectangle([(30, 30), (770, 1170)], outline=(197, 160, 89), width=4)

    # Brand Title
    draw.text((240, 100), "ARTISAN HILLS", fill=(218, 182, 116))
    draw.text((290, 150), "COORG ESTATE", fill=(160, 140, 110))

    # Generic name
    draw.rectangle([(120, 240), (680, 310)], fill=(38, 30, 27), outline=(197, 160, 89), width=2)
    draw.text((160, 260), "ROASTED WHOLE COFFEE BEANS", fill=(255, 255, 255))

    # Decorative icon
    draw.ellipse([(340, 380), (460, 500)], fill=(48, 38, 34), outline=(197, 160, 89), width=3)
    draw.text((365, 430), "100%", fill=(218, 182, 116))

    # Declarations Panel
    draw.rectangle([(80, 680), (720, 1140)], fill=(38, 30, 27), outline=(197, 160, 89), width=2)

    draw.text((120, 780), "Net Weight: 250 g", fill=(240, 240, 240))
    draw.text((120, 865), "MRP: ₹ 450.00 (inclusive of all taxes)", fill=(240, 240, 240))
    draw.text((120, 950), "Unit Sale Price: ₹ 1.80 / g", fill=(240, 240, 240))
    draw.text((120, 1020), "Packed On: 07/2026", fill=(240, 240, 240))
    draw.text((440, 1020), "Country of Origin: India", fill=(240, 240, 240))

    draw.text((90, 1080), "Mfd & Pkd by: Artisan Hills Coffee Roasters Pvt. Ltd., Coorg - 571201", fill=(200, 200, 200))
    draw.text((90, 1115), "Helpline: 1800-200-4545 | Email: support@artisancoffee.in", fill=(200, 200, 200))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, quality=92)
    print(f"Generated Coffee Label: {output_path}")

def draw_earbuds_label(output_path: str):
    # Sleek modern electronic packaging (800x1200)
    img = Image.new("RGB", (800, 1200), color=(245, 247, 250))
    draw = ImageDraw.Draw(img)

    # Blue header
    draw.rectangle([(0, 0), (800, 160)], fill=(15, 23, 42))
    draw.text((280, 50), "SOUNDWAVE", fill=(56, 189, 248))
    draw.text((260, 100), "AUDIO TECHNOLOGIES", fill=(148, 163, 184))

    # Product Title
    draw.text((140, 260), "TRUE WIRELESS STEREO EARBUDS", fill=(15, 23, 42))
    draw.text((220, 310), "Model: Pro Bass ANC", fill=(71, 85, 105))

    # Earbuds Graphic circle
    draw.ellipse([(280, 390), (520, 630)], fill=(226, 232, 240), outline=(56, 189, 248), width=4)
    draw.text((360, 500), "ANC 40dB", fill=(15, 23, 42))

    # Declarations Box
    draw.rectangle([(80, 720), (720, 1150)], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.text((120, 745), "Net Quantity: 1 N (1 Pair Earbuds, 1 Case)", fill=(30, 41, 59))
    draw.text((120, 840), "MRP: ₹ 2,999.00 (inclusive of all taxes)", fill=(30, 41, 59))
    draw.text((120, 935), "Month & Year of Import: 12/2028", fill=(220, 38, 38)) # Future date!
    draw.text((95, 1025), "Imported & Marketed by: Sonic Tech India Ltd, Gurugram - 122002", fill=(51, 65, 85))
    draw.text((95, 1110), "Toll Free: 1800-111-9999 | Email: help@sonictech.in", fill=(51, 65, 85))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, quality=92)
    print(f"Generated Earbuds Label: {output_path}")

if __name__ == "__main__":
    fixtures_dir = "backend/fixtures"
    draw_chips_label(os.path.join(fixtures_dir, "potato_chips_sample.jpg"))
    draw_coffee_label(os.path.join(fixtures_dir, "artisan_coffee_sample.jpg"))
    draw_earbuds_label(os.path.join(fixtures_dir, "wireless_earbuds_sample.jpg"))
