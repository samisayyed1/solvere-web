package SolvereSenseRequirements {
    doc /* Requirement usages for the budget- and interface-bearing requirements,
         short-named with the exact IDs from requirements/requirements.md.
         The full set of 66 requirements, with tests, is traced in
         requirements/trace.json. Values mirror params/params.toml. */

    private import ScalarValues::*;
    private import SolvereSense::*;

    requirement def PodRequirement {
        doc /* Base: every requirement here constrains the v1 pod. */
        subject pod : SolvereSensePod;
    }
    requirement def PowerCeiling :> PodRequirement {
        attribute maxPower : Power_W;
        attribute supplyVoltage : Voltage_V;
        attribute maxCurrent : Current_A;
    }
    requirement def MountEnvelope :> PodRequirement {
        attribute heightMin : Length_m;
        attribute heightMax : Length_m;
        attribute coverageSide : Length_m;
    }
    requirement def RetentionLoad :> PodRequirement {
        attribute loadFactor : Ratio;
    }
    requirement def CostCeiling :> PodRequirement {
        attribute maxCost : Cost_USD;
    }
    requirement def SensorKeepOut :> PodRequirement {
        attribute halfAngle : Angle_deg;
    }
    requirement def RadomeGap :> PodRequirement {
        attribute gapStep : Length_mm;
    }
    requirement def SensorLevel :> PodRequirement {
        attribute tolerance : Angle_deg;
    }
    requirement def ThermalLimit :> PodRequirement {
        attribute ambientMax : Temperature_degC;
        attribute sensorTempMax : Temperature_degC;
    }
    requirement def QualitativeRequirement :> PodRequirement;

    requirement <'REQ-SYS-001'> coverage : MountEnvelope {
        attribute :>> heightMin = 2.2;
        attribute :>> heightMax = 3.0;
        attribute :>> coverageSide = 3.0;
    }
    requirement <'REQ-SYS-002'> radomeNoDegradation : QualitativeRequirement;
    requirement <'REQ-MECH-004'> basePlateRetention : RetentionLoad {
        attribute :>> loadFactor = 4.0;
    }
    requirement <'REQ-MECH-005'> shellRetention : RetentionLoad {
        attribute :>> loadFactor = 4.0;
    }
    requirement <'REQ-MECH-006'> hiddenFastening : QualitativeRequirement;
    requirement <'REQ-MECH-007'> gasketGroovePresent : QualitativeRequirement;
    requirement <'REQ-MECH-009'> antennaLevel : SensorLevel {
        attribute :>> tolerance = 5.0;
    }
    requirement <'REQ-MECH-010'> metalFreeFov : SensorKeepOut {
        attribute :>> halfAngle = 60.0;
    }
    requirement <'REQ-MECH-013'> radomeThickness : QualitativeRequirement;
    requirement <'REQ-MECH-014'> antennaGap : RadomeGap {
        attribute :>> gapStep = 2.5;
    }
    requirement <'REQ-MECH-016'> twistOff : QualitativeRequirement;
    requirement <'REQ-MECH-017'> grooveSizing : QualitativeRequirement;
    requirement <'REQ-SYS-003'> twoPodInterference : QualitativeRequirement;
    requirement <'REQ-UX-004'> lightPipeFlush : QualitativeRequirement;
    requirement <'REQ-UX-005'> noWindowNoPinhole : QualitativeRequirement;
    requirement <'REQ-MECH-011'> strainRelief : QualitativeRequirement;
    requirement <'REQ-MECH-012'> cableExit : QualitativeRequirement;
    requirement <'REQ-PWR-001'> usbSupply : PowerCeiling {
        attribute :>> supplyVoltage = 5.0;
        attribute :>> maxCurrent = 1.0;
        attribute :>> maxPower = 5.0;
    }
    requirement <'REQ-PWR-003'> noBattery : QualitativeRequirement;
    requirement <'REQ-PWR-005'> powerCeiling : PowerCeiling {
        attribute :>> supplyVoltage = 5.0;
        attribute :>> maxCurrent = 1.0;
        attribute :>> maxPower = 1.4;
    }
    requirement <'REQ-ELEC-001'> noMains : QualitativeRequirement;
    requirement <'REQ-ENV-002'> sensorTemperature : ThermalLimit {
        attribute :>> ambientMax = 40.0;
        attribute :>> sensorTempMax = 85.0;
    }
    requirement <'REQ-EMC-005'> noExtraRadio : QualitativeRequirement;
    requirement <'REQ-COST-001'> prototypeCost : CostCeiling {
        attribute :>> maxCost = 50.0;
    }
    requirement <'REQ-COST-002'> productionCost : CostCeiling {
        attribute :>> maxCost = 30.0;
    }

    // Design intent (not evidence): which element is meant to satisfy each.
    satisfy coverage by pod;
    satisfy radomeNoDegradation by pod.radome;
    satisfy basePlateRetention by pod.basePlate;
    satisfy shellRetention by pod.shellToBase;
    satisfy hiddenFastening by pod.shellToBase;
    satisfy gasketGroovePresent by pod.groove;
    satisfy antennaLevel by pod.sensor;
    satisfy metalFreeFov by pod.radome;
    satisfy radomeThickness by pod.radome;
    satisfy antennaGap by pod.radome;
    satisfy strainRelief by pod.strainRelief;
    satisfy cableExit by pod.basePlate;
    satisfy usbSupply by pod.sensor.usbC;
    satisfy noBattery by pod;
    satisfy powerCeiling by pod.sensor;
    satisfy noMains by pod;
    satisfy sensorTemperature by pod;
    satisfy noExtraRadio by pod;
    satisfy prototypeCost by pod;
    satisfy twistOff by pod.shellToBase;
    satisfy grooveSizing by pod.groove;
    satisfy twoPodInterference by pod.sensor;
    satisfy lightPipeFlush by pod.lightPipe;
    satisfy noWindowNoPinhole by pod.shell;
    satisfy productionCost by pod;
}
