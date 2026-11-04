type Props = {
  tier: number;
  size?: number;
  paper?: boolean;
  muted?: boolean;
};

const FILL = ["#CFC6B4", "#C0503A", "#35996B", "#8A6ABE", "#C9E6EA"];

/** Five cuts. Silhouette first, colour second, name third. */
export function Gem({ tier, size = 40, paper = false, muted = false }: Props) {
  const index = Math.min(5, Math.max(1, tier)) - 1;
  const stroke = paper ? "#1A1108" : "#0E0B09";
  const fill = muted ? "none" : FILL[index];
  const weight = [1, 1.2, 1.4, 1.6, 1.8][index];

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      role="img"
      aria-label={["quartzo bruto", "granada cabochão", "esmeralda", "ametista", "diamante"][index]}
    >
      {index === 0 && (
        <>
          <path
            d="M14 40 L10 24 L22 11 L39 8 L52 18 L56 34 L44 52 L26 55 Z"
            fill={fill}
            stroke={stroke}
            strokeWidth={weight}
            strokeLinejoin="round"
          />
          <path d="M22 11 L24 33 L44 52 M10 24 L24 33 L56 34" fill="none" stroke={stroke} strokeWidth="1" opacity=".55" />
        </>
      )}
      {index === 1 && (
        <>
          <path d="M6 44 H58 A26 26 0 0 0 6 44 Z" fill={fill} stroke={stroke} strokeWidth={weight} />
          <path d="M18 32 A14 14 0 0 1 32 20" fill="none" stroke="#EADFC6" strokeWidth="1.6" opacity=".55" />
        </>
      )}
      {index === 2 && (
        <>
          <path d="M20 8 H44 L52 16 V48 L44 56 H20 L12 48 V16 Z" fill={fill} stroke={stroke} strokeWidth={weight} strokeLinejoin="round" />
          <path d="M24 16 H40 L44 20 V44 L40 48 H24 L20 44 V20 Z M28 24 H36 V40 H28 Z" fill="none" stroke={stroke} strokeWidth="1" opacity=".7" />
        </>
      )}
      {index === 3 && (
        <>
          <path d="M22 6 H42 L58 22 V42 L42 58 H22 L6 42 V22 Z" fill={fill} stroke={stroke} strokeWidth={weight} strokeLinejoin="round" />
          <path d="M32 6 V58 M6 32 H58" fill="none" stroke={stroke} strokeWidth="1" opacity=".55" />
        </>
      )}
      {index === 4 && (
        <>
          <path d="M32 6 L52 14 L58 32 L52 50 L32 58 L12 50 L6 32 L12 14 Z" fill={fill} stroke={stroke} strokeWidth={weight} strokeLinejoin="round" />
          <path d="M24 20 H40 L44 24 V40 L40 44 H24 L20 40 V24 Z" fill="none" stroke={stroke} strokeWidth="1.2" />
          <path
            d="M32 6 L24 20 M52 14 L40 20 M58 32 L44 24 M52 50 L40 40 M32 58 L24 44 M12 50 L20 40 M6 32 L20 24 M12 14 L24 20"
            fill="none"
            stroke={stroke}
            strokeWidth="1"
            opacity=".7"
          />
        </>
      )}
    </svg>
  );
}
