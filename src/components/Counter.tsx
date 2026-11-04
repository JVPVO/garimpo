import { useEffect, useRef, useState } from "react";

type Props = { value: number; duration?: number; suffix?: string };

/** Counts up once, in tabular numerals. Reduced motion jumps straight to the value. */
export function Counter({ value, duration = 620, suffix = "" }: Props) {
  const [shown, setShown] = useState(0);
  const frame = useRef(0);

  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) {
      setShown(value);
      return;
    }
    const start = performance.now();
    const step = (now: number) => {
      const progress = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - progress, 3);
      setShown(Math.round(value * eased));
      if (progress < 1) frame.current = requestAnimationFrame(step);
    };
    frame.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frame.current);
  }, [value, duration]);

  return (
    <span className="mono">
      {shown}
      {suffix}
    </span>
  );
}
