# TrackTag -- architecture notes

Blocks: a LiPo battery feeds a PMIC; the PMIC supplies 3.3 V to the MCU, the LTE-M modem and the GNSS receiver. The MCU talks to the modem over UART and to the GNSS receiver over I2C. The modem and GNSS each have their own antenna.

Budgets: total mass at most 45 g; average current at most 2 mA.
