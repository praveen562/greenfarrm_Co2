interface GrowthRingProps {
  score: number;
  category: string;
  size?: number;
}

const CATEGORY_COLORS: Record<string, string> = {
  Excellent: "#2C7350",
  Good: "#5FAD82",
  Moderate: "#C77D2B",
  "Needs Improvement": "#B23A2E",
};

export default function GrowthRing({ score, category, size = 160 }: GrowthRingProps) {
  const radius = size / 2 - 12;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color = CATEGORY_COLORS[category] ?? "#2C7350";

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#E4F2E9"
          strokeWidth={10}
          fill="none"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={10}
          strokeLinecap="round"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.8s ease" }}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="font-data text-3xl font-semibold text-ink">{score}</span>
        <span className="text-xs text-canopy-700">/ 100</span>
      </div>
    </div>
  );
}
