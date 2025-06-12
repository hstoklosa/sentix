const FEAR_GREED_LEVELS = [
  {
    min: 0,
    max: 24,
    label: "Extreme Fear",
    textColor: "text-destructive",
    bgColor: "bg-destructive",
  },
  {
    min: 25,
    max: 44,
    label: "Fear",
    textColor: "text-destructive/80",
    bgColor: "bg-destructive/80",
  },
  {
    min: 45,
    max: 54,
    label: "Neutral",
    textColor: "text-muted-foreground",
    bgColor: "bg-muted",
  },
  {
    min: 55,
    max: 74,
    label: "Greed",
    textColor: "text-chart-2/80",
    bgColor: "bg-chart-2/80",
  },
  {
    min: 75,
    max: 100,
    label: "Extreme Greed",
    textColor: "text-chart-2",
    bgColor: "bg-chart-2",
  },
];

type FearGreedProps = {
  value: number;
};

const getFearGreedLevel = (value: number) => {
  return (
    FEAR_GREED_LEVELS.find((level) => value >= level.min && value <= level.max) ||
    FEAR_GREED_LEVELS[2]
  ); // Default to Neutral
};

const FearGreedIndicator = ({ value }: FearGreedProps) => {
  const level = getFearGreedLevel(value);
  return <span className={`text-sm ${level.textColor}`}>{level.label}</span>;
};

const FearGreedMeter = ({ value }: FearGreedProps) => {
  const level = getFearGreedLevel(value);
  return (
    <div className="w-[80%] h-3 bg-secondary rounded-full overflow-hidden">
      <div
        className={`h-full ${level.bgColor} rounded-full`}
        style={{ width: `${value}%` }}
      />
    </div>
  );
};

export { FearGreedIndicator, FearGreedMeter };
