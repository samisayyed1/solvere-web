package TrackTag {
    doc /* TrackTag architecture (docs/architecture.md). */
    import ScalarValues::*;

    attribute def Mass :> ScalarValues::Real;
    attribute def Current :> ScalarValues::Real;

    port def PowerPort;
    port def UartPort;
    port def I2cPort;

    part def Battery { port pwrOut : PowerPort; attribute mass : Mass; }
    part def Pmic { port pwrIn : PowerPort; port rail3v3 : PowerPort; attribute mass : Mass; }
    part def Mcu { port pwr : PowerPort; port uart : UartPort; port i2c : I2cPort; attribute mass : Mass; }
    part def Modem { port pwr : PowerPort; port uart : UartPort; attribute mass : Mass; }
    part def Gnss { port pwr : PowerPort; port i2c : I2cPort; attribute mass : Mass; }

    requirement def MassLimit {
        doc /* REQ-SYS-001: the TrackTag shall weigh at most 45 g. */
        attribute maxMass : Mass;
    }
    requirement def AverageCurrent {
        doc /* REQ-SYS-002: at most 2 mA average in tracking mode. */
        attribute maxCurrent : Current;
    }

    part def TrackTagSystem {
        part battery : Battery;
        part pmic : Pmic;
        part mcu : Mcu;
        part modem : Modem;
        part gnss : Gnss;
        connect battery.pwrOut to pmic.pwrIn;
        connect pmic.rail3v3 to mcu.pwr;
        connect pmic.rail3v3 to modem.pwr;
        connect pmic.rail3v3 to gnss.pwr;
        connect mcu.uart to modem.uart;
        connect mcu.i2c to gnss.i2c;
        requirement massLimit : MassLimit { attribute :>> maxMass = 45; }
        requirement avgCurrent : AverageCurrent { attribute :>> maxCurrent = 2; }
    }
}
