# Draft: questions to Seeed (for the owner to send)

Owner round 2 (Q-18): Forge drafts, the owner sends. Contact given in DS p.4: iot@seeed.cc. Nothing below has been sent. Each answer retires the assumption or risk named in brackets.

---

**Subject:** MR60FDA2 kit (SKU 114993388): technical and volume questions for a ceiling-mounted product

Hello,

We are designing a ceiling enclosure around the XIAO 60GHz mmWave MR60FDA2 kit (SKU 114993388), used as-is, for home-automation use in bedrooms and living rooms. We have the kit datasheet (updated 2026-07-30), the module technical specification (Beta V1.0, 2024-03-05) and the wiki. Could you help with the following?

1. **Tilt tolerance:** what is the allowed tilt of the antenna face from horizontal when ceiling-mounted? (The MR60FDA1 wiki gives ≤5°; we found nothing for the MR60FDA2.) [A-002]
2. **Field of view:** the kit datasheet gives 120° x 100°, the wiki features list 100° x 40°, and the module specification a -3 dB beam of ±60° in both planes. Which should we design to? [R-013]
3. **Operating temperature of the kit:** the module is rated -20 °C to 85 °C and the XIAO -40 °C to 85 °C. What is the rating of the complete kit, including the BH1750, WS2812 and carrier board? [A-004]
4. **Power:** are the datasheet figures (0.5 W standby, 0.8 W active, 1.4 W with a Grove relay) whole-kit input power at the USB-C port? What is the peak input current? The module specification gives 600 mA for the radar module. [A-007, R-014]
5. **Mechanical drawing:** can you share a drawing of the kit carrier board (outline, stack height with the XIAO, mounting holes, LED and reset-button positions) and the kit weight? [A-005]
6. **Two sensors in one room:** the wiki warns against radars installed too close together. What minimum spacing do you recommend between two MR60FDA2 sensors in one room, and does the FCC co-location note on the datasheet apply to two separate devices? [R-007]
7. **Room types and occupancy:** the module specification describes use in bathrooms and single-person scenes. Is bedroom and living-room use supported, and how does the fall-event output behave with two people present? [R-004]
8. **USB-C:** does the XIAO ESP32C6 start from a USB-C-to-C cable on a Type-C wall adapter (CC pull-downs fitted)? [R-012]
9. **Certification:** what FCC ID or other radio approvals cover the kit, and do they cover it when fitted inside a plastic enclosure? [REQ-EMC-002]
10. **Volume and lifecycle:** what is the price at 100, 500 and 1,000 units, the lead time, and the expected lifecycle? Where are change notices (PCN-114993388) published? [R-002, R-009]

Thank you,
<owner name>
