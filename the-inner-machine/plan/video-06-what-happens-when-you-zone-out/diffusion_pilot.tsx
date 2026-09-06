/* @jsxImportSource @diffusionstudio/jsx */
// Generated pilot: selective emphasis only; blank beats have no text node.
export default function VideoPilot() {
  return (
    <stage>
      <scene name="Pilot" width={1920} height={1080} fill="#10122E" active>
        <image id="beat_01" src="images/beat_01.jpg" x={0} y={0} width={1920} height={1080} start={0.000} end={4.400} />
        <image id="beat_02" src="images/beat_02.jpg" x={0} y={0} width={1920} height={1080} start={4.400} end={8.800} />
        <text id="emphasis_02" width={1920} height={1080} textAlign="center" textBaseline="middle" fontSize={112} fontWeight="bold" color="#E0A458" start={5.940} end={7.700}>ATTENTION</text>
        <image id="beat_03" src="images/beat_03.jpg" x={0} y={0} width={1920} height={1080} start={8.800} end={13.200} />
        <audio id="narration" src="narration.wav" start={0} end={13.200} />
      </scene>
    </stage>
  );
}
