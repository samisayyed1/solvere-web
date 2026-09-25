export default () => (
  <board>
    <chip
      name="U1"
      footprint="sot23_3"
      pinLabels={{ pin1: "GND", pin2: "VOUT", pin3: "VIN" }}
      manufacturerPartNumber="AMS1117-3.3"
    />
    <capacitor name="C_IN" capacitance="1uF" footprint="0402" />
    <capacitor name="C_OUT" capacitance="1uF" footprint="0402" />

    <trace from=".C_IN > .pin1" to=".U1 > .VIN" />
    <trace from=".C_IN > .pin2" to=".U1 > .GND" />
    <trace from=".C_OUT > .pin1" to=".U1 > .VOUT" />
  </board>
)
