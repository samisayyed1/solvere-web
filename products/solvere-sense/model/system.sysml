package SolvereSense {
    doc /* Solvere Sense ceiling pod, v1 (bedroom / living room), G0 draft.
         Structure, interfaces and budgets only; geometry lives in cad/ and
         every number mirrors params/params.toml (the source of truth).
         Requirement IDs are the REQ-<AREA>-<NNN> IDs in
         requirements/requirements.md; linkage is in requirements.sysml
         and requirements/trace.json. Evidence level: L0/L1 (structure
         parses; nothing here is measured). Sources: docs/sources/README.md.
         Masses are not modelled: no mass is sourced yet (docs/budgets.md). */

    private import ScalarValues::*;

    // ---- value types (units in the attribute names; SI except mm) ----
    attribute def Voltage_V :> ScalarValues::Real;
    attribute def Current_A :> ScalarValues::Real;
    attribute def Power_W :> ScalarValues::Real;
    attribute def Length_m :> ScalarValues::Real;
    attribute def Length_mm :> ScalarValues::Real;
    attribute def Angle_deg :> ScalarValues::Real;
    attribute def Temperature_degC :> ScalarValues::Real;
    attribute def Cost_USD :> ScalarValues::Real;
    attribute def Ratio :> ScalarValues::Real;

    // ---- items that flow across interfaces ----
    item def DCPower;
    item def RadarSignal;
    item def MechanicalLoad;
    item def SensorData;
    item def StatusLight;

    // ---- ports ----
    port def UsbCPowerPort {
        doc /* USB-C power input, 5 V / 1 A (REQ-PWR-001, REQ-PWR-004). */
        attribute voltage : Voltage_V;
        attribute currentMax : Current_A;
        in item power : DCPower;
    }
    port def CeilingFixPort {
        doc /* Base plate to ceiling: screws with drywall anchors or concrete plugs (REQ-MECH-001/-002). */
        out item load : MechanicalLoad;
    }
    port def TBarPort {
        doc /* Optional clip to drop-ceiling T-bar grid (REQ-MECH-003). */
        out item load : MechanicalLoad;
    }
    port def ShellBasePort {
        doc /* Hidden shell-to-base fastening; no screw through the shell (REQ-MECH-006). */
        out item load : MechanicalLoad;
    }
    port def GasketGroovePort {
        doc /* Continuous perimeter groove on the shell-to-base joint, present in every variant (REQ-MECH-007). */
    }
    port def RadomeWindowPort {
        doc /* 60 GHz radar path through the radome; metal-free inside the FoV (REQ-MECH-010, REQ-SYS-002). */
        inout item signal : RadarSignal;
    }
    port def CableExitPort {
        doc /* USB cable exit at the ceiling plane into the adhesive raceway (REQ-MECH-012). */
    }
    port def LedLightPort {
        doc /* Visible light from the kit status LED into the light pipe (REQ-UX-004). */
        out item light : StatusLight;
    }
    port def WirelessDataPort {
        doc /* XIAO ESP32C6 radio: 2.4 GHz Wi-Fi 6, Bluetooth LE, IEEE 802.15.4 (XIAO wiki).
             Which radios are enabled and where data goes is open (Q-01, Q-02).
             Credentials: REQ-FW-002, REQ-FW-003. */
        out item data : SensorData;
    }

    // ---- interfaces ----
    interface def ShellBaseInterface {
        doc /* Base plate <-> shell. Retains 4x shell+kit weight for 60 s (REQ-MECH-005). */
        end baseSide : ShellBasePort;
        end shellSide : ~ShellBasePort;
    }
    interface def GasketGrooveInterface {
        doc /* Groove on the base-plate side mates with the shell rim; gasket only in the bathroom variant. */
        end grooveSide : GasketGroovePort;
        end rimSide : ~GasketGroovePort;
    }
    interface def UsbPowerInterface {
        doc /* External USB wall adapter <-> pod USB-C input. */
        end source : ~UsbCPowerPort;
        end sink : UsbCPowerPort;
    }

    // ---- parts ----
    part def BasePlate {
        doc /* Screw-on ceiling plate; carries the gasket groove and cable exit. */
        port ceiling : CeilingFixPort;
        port toShell : ShellBasePort;
        port groove : GasketGroovePort;
        port cableExit : CableExitPort;
    }
    part def Shell {
        doc /* Matte warm-white room-facing cover (REQ-UX-001, REQ-UX-002). Wall
             thickness is a G1 choice bounded by params mfg.fdm.min_wall. */
        port toBase : ~ShellBasePort;
        port rim : ~GasketGroovePort;
    }
    part def Radome {
        doc /* RF window over the antenna. Thickness = N x half-wavelength in the
             material (MDS s8, REQ-MECH-013), set by coupon test; antenna gap =
             N x 2.5 mm (REQ-MECH-014). */
        attribute antennaGapStep_mm : Length_mm;
        attribute keepOutHalfAngle : Angle_deg;
        port window : ~RadomeWindowPort;
    }
    part def GasketGroove {
        doc /* Groove feature of the base plate; dimensions pending gasket choice and ingress target (Q-08). */
    }
    part def Gasket {
        doc /* Bathroom variant only: O-ring cord for IPX4 (REQ-MECH-008, -017, -018;
             Owner round 2). Not fitted in v1. Gland per ARSDG Table A. */
        attribute squeezeMin_pct : ScalarValues::Real;
        attribute squeezeMax_pct : ScalarValues::Real;
    }
    part def UsbCReceptacle {
        doc /* The kit's on-board USB-C connector (use as-is pending Q-01). */
        port power : UsbCPowerPort;
    }
    part def SensorKit {
        doc /* Seeed MR60FDA2 kit, SKU 114993388 (DS p.1, p.7): 60 GHz radar module
             with BH1750 light sensor, WS2812 LED, reset button and Grove port
             (DS p.2, p.6) + XIAO ESP32C6 (Wi-Fi 6, Bluetooth LE, 802.15.4; XIAO wiki). */
        attribute supplyVoltage : Voltage_V;
        attribute freqMin_GHz : ScalarValues::Real;
        attribute freqMax_GHz : ScalarValues::Real;
        attribute beamHalfAngle : Angle_deg;
        attribute powerStandby : Power_W;
        attribute powerActive : Power_W;
        attribute powerMax : Power_W;
        attribute fovHorizontal : Angle_deg;
        attribute fovVertical : Angle_deg;
        attribute levelTolerance : Angle_deg;
        attribute operatingTempMax : Temperature_degC;
        attribute unitPrice : Cost_USD;
        part usbC : UsbCReceptacle;
        port antenna : RadomeWindowPort;
        port radio : WirelessDataPort;
        port led : ~LedLightPort;
    }
    part def CableStrainRelief {
        doc /* Clamps the USB cable jacket (REQ-MECH-011). */
    }
    part def TBarClipAdapter {
        doc /* Optional drop-ceiling adapter for 15 mm and 24 mm grids (REQ-MECH-003, Owner round 2). */
        attribute gridWidthNarrow_mm : Length_mm;
        attribute gridWidthWide_mm : Length_mm;
        port grid : TBarPort;
    }
    part def LightPipe {
        doc /* Flush, matte warm-white light pipe from the kit WS2812 LED to the shell
             surface; LED off in normal use (REQ-UX-004, REQ-FW-004..006). No
             light-sensor window, no reset pinhole (REQ-UX-005). */
        port fromLed : LedLightPort;
    }
    part def Room {
        doc /* One room holds one or two pods (Owner round 2, REQ-SYS-003, REQ-MNT-006).
             Radar-to-radar interference is checked by TP-SYS-003. */
        attribute maxPods : ScalarValues::Integer;
        part pods : SolvereSensePod [1..2];
    }
    part def ExternalUsbAdapter {
        doc /* Standard USB wall adapter, outside the system boundary (supply in box: Q-13). */
        port usbOut : ~UsbCPowerPort;
    }

    part def SolvereSensePod {
        doc /* v1 pod. Contains no battery (REQ-PWR-003) and no mains conductor (REQ-ELEC-001). */
        attribute mountHeightMin : Length_m;
        attribute mountHeightMax : Length_m;
        attribute coverageSide : Length_m;
        attribute retentionLoadFactor : Ratio;
        // power budget (docs/budgets.md)
        attribute supplyPowerAvailable : Power_W;
        attribute podPowerMax : Power_W;
        // thermal budget (docs/budgets.md)
        attribute maxThermalResistance_KperW : ScalarValues::Real;
        // cost budget
        attribute prototypeCostMax : Cost_USD;
        attribute productionBomMax : Cost_USD;

        part basePlate : BasePlate;
        part shell : Shell;
        part radome : Radome;
        part groove : GasketGroove;
        part gasket : Gasket [0..1];
        part sensor : SensorKit;
        part strainRelief : CableStrainRelief;
        part tBarClip : TBarClipAdapter [0..1];
        part lightPipe : LightPipe;

        interface shellToBase : ShellBaseInterface connect basePlate.toShell to shell.toBase;
        interface grooveToRim : GasketGrooveInterface connect basePlate.groove to shell.rim;
        connection rfPath connect sensor.antenna to radome.window;
        connection ledPath connect sensor.led to lightPipe.fromLed;
    }

    // ---- the configured v1 instance, values mirror params/params.toml ----
    part pod : SolvereSensePod {
        attribute :>> mountHeightMin = 2.2;        // m, params mount.height_min
        attribute :>> mountHeightMax = 3.0;        // m, params mount.height_max
        attribute :>> coverageSide = 3.0;          // m, params mount.coverage_side (A-011)
        attribute :>> retentionLoadFactor = 4.0;   // 1, params mount.retention_load_factor (A-001)
        attribute :>> supplyPowerAvailable = 5.0;  // W = 5 V x 1 A, params power.usb_*
        attribute :>> podPowerMax = 1.4;           // W, params power.pod_power_max (A-008)
        attribute :>> maxThermalResistance_KperW = 32.1; // K/W, params thermal.max_thermal_resistance (40 degC ambient)
        attribute :>> prototypeCostMax = 50.0;     // USD, params cost.prototype_max
        attribute :>> productionBomMax = 30.0;     // USD, params cost.production_bom_max
        part :>> tBarClip {
            attribute :>> gridWidthNarrow_mm = 15.0; // mm, params tbar.grid_width_narrow (Owner round 2)
            attribute :>> gridWidthWide_mm = 24.0;   // mm, params tbar.grid_width_wide (Owner round 2)
        }
        part :>> gasket {
            attribute :>> squeezeMin_pct = 10.0;     // %, params gasket.static_squeeze_min (ARSDG p.113)
            attribute :>> squeezeMax_pct = 40.0;     // %, params gasket.static_squeeze_max (ARSDG p.113)
        }
        part :>> radome {
            attribute :>> antennaGapStep_mm = 2.5; // mm, params radome.antenna_gap_step (MDS p.12)
            attribute :>> keepOutHalfAngle = 60.0; // deg, params radome.keepout_half_angle (MDS p.4)
        }
        part :>> sensor {
            attribute :>> supplyVoltage = 5.0;     // V, params sensor.supply_voltage (DS p.6)
            attribute :>> freqMin_GHz = 58.0;      // GHz, params sensor.freq_min (MDS p.4)
            attribute :>> freqMax_GHz = 62.0;      // GHz, params sensor.freq_max (MDS p.4)
            attribute :>> beamHalfAngle = 60.0;    // deg, params sensor.beam_half_angle (MDS p.4)
            attribute :>> powerStandby = 0.5;      // W, DS p.6
            attribute :>> powerActive = 0.8;       // W, DS p.6
            attribute :>> powerMax = 1.4;          // W, DS p.6 (with Grove relay)
            attribute :>> fovHorizontal = 120.0;   // deg, DS p.6
            attribute :>> fovVertical = 100.0;     // deg, DS p.6 (MDS p.4 gives 120, R-013)
            attribute :>> levelTolerance = 5.0;    // deg, params sensor.level_tolerance (A-002)
            attribute :>> operatingTempMax = 85.0; // degC, params sensor.kit_temp_max (A-004)
            attribute :>> unitPrice = 28.99;       // USD at 10+, params sensor.unit_price_web_qty10
        }
    }

    part room : Room {
        attribute :>> maxPods = 2;                 // params pods.max_per_room (Owner round 2)
    }

    part adapter : ExternalUsbAdapter;
    interface powerFeed : UsbPowerInterface connect adapter.usbOut to pod.sensor.usbC.power;
}
