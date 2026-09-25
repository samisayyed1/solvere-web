package LadderFixture {
    doc /* Ladder fixture system model (plugins/forge/tests/ladder). Must parse
         with zero errors and zero warnings under
         `~/.forge/bin/spec42 check model/system.sysml` (REQ-SYS-001). */

    import ScalarValues::*;

    attribute def Length :> ScalarValues::Real;
    attribute def Voltage :> ScalarValues::Real;

    part def MountingPlate {
        doc /* cad/plate.py, dimensions from params/params.toml. */
        attribute thickness : Length;
    }

    part def DividerBoard {
        doc /* ecad/divider, simulated in analysis/spice/divider.cir. */
        attribute vout : Voltage;
    }

    part def Product {
        part plate : MountingPlate;
        part board : DividerBoard;
    }

    requirement def DividerOutput {
        doc /* REQ-ELEC-001: output within [minVout, maxVout]. */
        attribute minVout : Voltage;
        attribute maxVout : Voltage;
    }

    part product : Product {
        requirement dividerOutput : DividerOutput {
            attribute :>> minVout = 2.45;
            attribute :>> maxVout = 2.55;
        }
    }
}
