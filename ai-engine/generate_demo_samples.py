"""
Generate controlled demo sample images for SIH presentation and pitch rehearsals.
Creates 5 compliant and 5 non-compliant commodity package label images.
"""

import os
import cv2
import numpy as np


def create_label(filename: str, lines: list, width: int = 750, height: int = 420):
    img = np.ones((height, width, 3), dtype=np.uint8) * 255
    # Light gray border to simulate packaging box
    cv2.rectangle(img, (5, 5), (width - 5, height - 5), (220, 220, 220), 2)

    for text, origin, scale, color, thickness in lines:
        cv2.putText(img, text, origin, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    cv2.imwrite(filename, img)
    print(f"Created: {filename}")


def main():
    # -------------------------------------------------------------
    # Compliant Samples (samples/compliant/)
    # -------------------------------------------------------------
    create_label(
        "samples/compliant/demo_product_01.jpg",
        [
            ("Parle-G Gold Biscuits", (30, 45), 1.0, (0, 0, 0), 2),
            ("Manufactured by: Parle Products Pvt. Ltd.", (30, 90), 0.7, (0, 0, 0), 2),
            ("Net Wt: 100g", (30, 135), 0.8, (0, 0, 0), 2),
            ("MRP Rs. 20.00 (incl. of all taxes)", (30, 180), 0.8, (0, 0, 0), 2),
            ("Mfg Date: 03/2026", (30, 225), 0.8, (0, 0, 0), 2),
            ("Customer Care: 1800-22-2211", (30, 270), 0.7, (0, 0, 0), 2),
            ("Country of Origin: India", (30, 315), 0.8, (0, 0, 0), 2),
            ("Best Before 6 months from Mfg", (30, 355), 0.7, (0, 0, 0), 2),
            ("Unit Sale Price: Rs. 0.20 / g", (30, 395), 0.7, (0, 0, 0), 2)
        ],
        width=750, height=420
    )

    create_label(
        "samples/compliant/demo_product_02.jpg",
        [
            ("Real Mixed Fruit Juice", (30, 45), 1.0, (0, 0, 0), 2),
            ("Marketed by: Dabur India Ltd.", (30, 90), 0.7, (0, 0, 0), 2),
            ("Net Quantity: 1 L", (30, 135), 0.8, (0, 0, 0), 2),
            ("MRP Rs. 130.00 (incl. of all taxes)", (30, 180), 0.8, (0, 0, 0), 2),
            ("Packed on: 01/2026", (30, 225), 0.8, (0, 0, 0), 2),
            ("Feedback: 1800-103-1644", (30, 270), 0.7, (0, 0, 0), 2),
            ("Country of Origin: India", (30, 315), 0.8, (0, 0, 0), 2),
            ("Best Before 12 months from packing", (30, 355), 0.7, (0, 0, 0), 2),
            ("Unit Sale Price: Rs. 0.13 / ml", (30, 395), 0.7, (0, 0, 0), 2)
        ],
        width=750, height=420
    )

    create_label(
        "samples/compliant/demo_product_03.jpg",
        [
            ("Tata Salt Vacuum Evaporated", (30, 50), 0.9, (0, 0, 0), 2),
            ("Manufactured by: Tata Consumer Products Ltd.", (30, 100), 0.7, (0, 0, 0), 2),
            ("Net Wt: 1 kg", (30, 145), 0.8, (0, 0, 0), 2),
            ("MRP Rs. 28.00", (30, 190), 0.8, (0, 0, 0), 2),
            ("Date of Manufacture: 02/2026", (30, 235), 0.8, (0, 0, 0), 2),
            ("Consumer Care: 1800-345-1720", (30, 280), 0.7, (0, 0, 0), 2),
            ("Product of India", (30, 320), 0.8, (0, 0, 0), 2),
            ("Best Before 24 months", (30, 360), 0.7, (0, 0, 0), 2),
            ("Unit Sale Price: Rs. 0.03 / g", (30, 400), 0.7, (0, 0, 0), 2)
        ],
        width=750, height=430
    )

    create_label(
        "samples/compliant/demo_product_04.jpg",
        [
            ("Dettol Original Liquid Handwash", (30, 50), 0.9, (0, 0, 0), 2),
            ("Manufactured by: Reckitt Benckiser India", (30, 95), 0.7, (0, 0, 0), 2),
            ("Net Volume: 200 ml", (30, 140), 0.8, (0, 0, 0), 2),
            ("MRP Rs. 99.00 (inclusive of taxes)", (30, 185), 0.8, (0, 0, 0), 2),
            ("Mfg: 12/2025", (30, 230), 0.8, (0, 0, 0), 2),
            ("Toll Free: 1800-102-2221", (30, 275), 0.7, (0, 0, 0), 2),
            ("Made in India", (30, 315), 0.8, (0, 0, 0), 2),
            ("Use Before: 11/2027", (30, 355), 0.7, (0, 0, 0), 2),
            ("USP: Rs. 0.50 per ml", (30, 395), 0.7, (0, 0, 0), 2)
        ],
        width=750, height=420
    )

    create_label(
        "samples/compliant/demo_product_05.jpg",
        [
            ("Ferrero Rocher Hazelnut Chocolates", (30, 50), 0.9, (0, 0, 0), 2),
            ("Imported by: Ferrero India Pvt. Ltd.", (30, 95), 0.7, (0, 0, 0), 2),
            ("Net Wt: 200g (16 pieces)", (30, 140), 0.8, (0, 0, 0), 2),
            ("MRP Rs. 549.00 (incl. taxes)", (30, 185), 0.8, (0, 0, 0), 2),
            ("Packed: 01/2026", (30, 230), 0.8, (0, 0, 0), 2),
            ("Consumer Care: 1800-209-1200", (30, 275), 0.7, (0, 0, 0), 2),
            ("Country of Origin: Italy", (30, 315), 0.8, (0, 0, 0), 2),
            ("Best Before 9 months from pack", (30, 355), 0.7, (0, 0, 0), 2),
            ("Unit Sale Price: Rs. 2.75 / g", (30, 395), 0.7, (0, 0, 0), 2)
        ],
        width=750, height=420
    )

    # -------------------------------------------------------------
    # Non-Compliant / Violation Samples (samples/noncompliant/)
    # -------------------------------------------------------------
    # 6: Missing MRP declaration
    create_label(
        "samples/noncompliant/demo_product_06.jpg",
        [
            ("Kurkure Masala Munch", (30, 50), 1.0, (0, 0, 0), 2),
            ("Mfd by: PepsiCo India Holdings Pvt. Ltd.", (30, 100), 0.7, (0, 0, 0), 2),
            ("Net Wt: 85g", (30, 150), 0.8, (0, 0, 0), 2),
            # NO MRP
            ("Mfg Date: 02/2026", (30, 200), 0.8, (0, 0, 0), 2),
            ("Consumer Cell: 1800-22-4020", (30, 250), 0.7, (0, 0, 0), 2),
            ("Country of Origin: India", (30, 300), 0.8, (0, 0, 0), 2),
            ("Best Before 4 months", (30, 345), 0.7, (0, 0, 0), 2)
        ],
        width=750, height=400
    )

    # 7: Missing Manufacturer Address
    create_label(
        "samples/noncompliant/demo_product_07.jpg",
        [
            ("Everest Garam Masala", (30, 50), 1.0, (0, 0, 0), 2),
            # NO MANUFACTURER
            ("Net Wt: 100g", (30, 105), 0.8, (0, 0, 0), 2),
            ("MRP Rs. 82.00", (30, 155), 0.8, (0, 0, 0), 2),
            ("Mfg Date: 12/2025", (30, 205), 0.8, (0, 0, 0), 2),
            ("Contact: customercare@everestspices.com", (30, 255), 0.7, (0, 0, 0), 2),
            ("Product of India", (30, 305), 0.8, (0, 0, 0), 2),
            ("Best Before 12 months", (30, 350), 0.7, (0, 0, 0), 2)
        ],
        width=750, height=400
    )

    # 8: Missing Consumer Care
    create_label(
        "samples/noncompliant/demo_product_08.jpg",
        [
            ("Haldiram Bhujia Sev", (30, 50), 1.0, (0, 0, 0), 2),
            ("Manufactured by: Haldiram Snacks Pvt. Ltd.", (30, 105), 0.7, (0, 0, 0), 2),
            ("Net Wt: 200g", (30, 155), 0.8, (0, 0, 0), 2),
            ("MRP Rs. 55.00", (30, 205), 0.8, (0, 0, 0), 2),
            ("Mfg Date: 01/2026", (30, 255), 0.8, (0, 0, 0), 2),
            # NO CONSUMER CARE
            ("Country of Origin: India", (30, 305), 0.8, (0, 0, 0), 2),
            ("Best Before 6 months", (30, 350), 0.7, (0, 0, 0), 2)
        ],
        width=750, height=400
    )

    # 9: Missing Net Quantity
    create_label(
        "samples/noncompliant/demo_product_09.jpg",
        [
            ("Premium Basmati Rice", (30, 50), 1.0, (0, 0, 0), 2),
            ("Packed by: KRBL Ltd., Noida, UP", (30, 105), 0.7, (0, 0, 0), 2),
            # NO NET QUANTITY
            ("MRP Rs. 195.00", (30, 155), 0.8, (0, 0, 0), 2),
            ("Packed on: 02/2026", (30, 205), 0.8, (0, 0, 0), 2),
            ("Consumer Care: 1800-102-4725", (30, 255), 0.7, (0, 0, 0), 2),
            ("Made in India", (30, 305), 0.8, (0, 0, 0), 2),
            ("Best Before 24 months", (30, 350), 0.7, (0, 0, 0), 2)
        ],
        width=750, height=400
    )

    # 10: Missing Country of Origin
    create_label(
        "samples/noncompliant/demo_product_10.jpg",
        [
            ("Swiss Dark Chocolate 70%", (30, 50), 1.0, (0, 0, 0), 2),
            ("Imported by: Global Sweets Pvt. Ltd.", (30, 105), 0.7, (0, 0, 0), 2),
            ("Net Weight: 100g", (30, 155), 0.8, (0, 0, 0), 2),
            ("MRP Rs. 290.00", (30, 205), 0.8, (0, 0, 0), 2),
            ("Mfg: 11/2025", (30, 255), 0.8, (0, 0, 0), 2),
            ("Email: help@globalsweets.in", (30, 305), 0.7, (0, 0, 0), 2),
            # NO COUNTRY OF ORIGIN
            ("Best Before 12 months", (30, 350), 0.7, (0, 0, 0), 2)
        ],
        width=750, height=400
    )

    # -------------------------------------------------------------
    # Multi-Image Samples (Front, Back, Side)
    # -------------------------------------------------------------
    create_label(
        "samples/compliant/demo_product_01_front.jpg",
        [
            ("Parle-G Gold Biscuits", (30, 80), 1.2, (0, 0, 0), 2),
            ("Net Wt: 100g", (30, 160), 1.0, (0, 0, 0), 2),
        ],
        width=700, height=350
    )

    create_label(
        "samples/compliant/demo_product_01_back.jpg",
        [
            ("MRP Rs. 20.00 (incl. of all taxes)", (30, 50), 0.8, (0, 0, 0), 2),
            ("Mfg Date: 03/2026", (30, 100), 0.8, (0, 0, 0), 2),
            ("Best Before 6 months from Mfg", (30, 150), 0.7, (0, 0, 0), 2),
            ("Unit Sale Price: Rs. 0.20 / g", (30, 200), 0.7, (0, 0, 0), 2),
            ("Manufactured by: Parle Products Pvt. Ltd.", (30, 250), 0.7, (0, 0, 0), 2),
        ],
        width=700, height=350
    )

    create_label(
        "samples/compliant/demo_product_01_side.jpg",
        [
            ("Customer Care: 1800-22-2211", (30, 80), 0.8, (0, 0, 0), 2),
            ("Country of Origin: India", (30, 160), 0.9, (0, 0, 0), 2),
        ],
        width=700, height=350
    )

    print("\nAll demo product images generated successfully!")


if __name__ == "__main__":
    main()

