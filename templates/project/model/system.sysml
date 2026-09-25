package ProductSystem {
    doc /* Tiny starter systems model for a Forge product-engineering project
         (CONTRACTS.md sections 1 and 9). Replace with the real system model
         as requirements and the architecture firm up; keep it parsing with
         zero errors and zero warnings under
         `~/.forge/bin/spec42 check model/system.sysml`. */

    import ScalarValues::*;

    attribute def Mass :> ScalarValues::Real;
    attribute def Force :> ScalarValues::Real;

    part def Enclosure {
        doc /* The product enclosure (built in cad/, dimensions from params/params.toml). */
        attribute mass : Mass;
    }

    part def Product {
        doc /* Root product definition. */
        part enclosure : Enclosure;
    }

    requirement def SnapFitRetention {
        doc /* REQ-MECH-001: the enclosure shall retain the lid with a
             snap-fit engagement force within [minForce, maxForce]. */
        attribute minForce : Force;
        attribute maxForce : Force;
    }

    part product : Product {
        requirement snapFitRetention : SnapFitRetention {
            attribute :>> minForce = 15;
            attribute :>> maxForce = 40;
        }
    }
}
