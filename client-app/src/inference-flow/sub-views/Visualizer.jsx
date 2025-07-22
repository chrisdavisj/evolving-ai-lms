import "./Visualizer.css";

export default function Visualizer({ volume }) {
  const intensity = Math.floor((volume / 100) * 255);
  const color = `rgb(${intensity}, ${255 - intensity}, 80)`;
  const height = 100;
  const barWidth = `${Math.max(volume, 5)}%`;

  return (
    <div className="visualizer-horizontal-container">
      <div
        className="visualizer-horizontal-bar"
        style={{
          width: barWidth,
          backgroundColor: color
        }}
      />
    </div>
  );
}
