interface ProgressBarProps {
  percent: number;
}

export default function ProgressBar({ percent }: ProgressBarProps) {
  return (
    <div className="w-full bg-stone-100 rounded-full h-2.5 my-3 overflow-hidden">
      <div
        className="bg-action h-2.5 rounded-full transition-all duration-500 ease-out"
        style={{ width: `${Math.min(100, Math.max(0, percent))}%` }}
      />
    </div>
  );
}
