/** The mine collar: a woodcut timber frame around the mouth of the shaft. */
export function Collar() {
  return (
    <svg width="148" height="118" viewBox="0 0 148 118" role="img" aria-label="boca da mina">
      <defs>
        <linearGradient id="shaftShade" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#0E0B09" />
          <stop offset="0.55" stopColor="#171210" />
          <stop offset="1" stopColor="#221A14" />
        </linearGradient>
        <pattern id="grain" width="9" height="9" patternUnits="userSpaceOnUse">
          <path d="M0 4.5h9" stroke="#423325" strokeWidth="0.7" opacity="0.55" />
        </pattern>
      </defs>

      {/* shaft opening */}
      <path d="M30 34 H118 V118 H30 Z" fill="url(#shaftShade)" />
      <path d="M30 34 H118 V118 H30 Z" fill="url(#grain)" opacity="0.5" />
      {/* cleats inside the shaft */}
      <g stroke="#423325" strokeWidth="2" opacity="0.8">
        <path d="M30 52 H118" />
        <path d="M30 74 H118" />
        <path d="M30 96 H118" />
      </g>
      {/* faint lamp light falling in */}
      <path d="M40 34 L74 118 H108 L74 34 Z" fill="#F2B65A" opacity="0.07" />

      {/* timber frame */}
      <g stroke="#6B5539" strokeLinejoin="round">
        <path d="M10 30 H138 V44 H10 Z" fill="#3A2C20" strokeWidth="1.4" />
        <path d="M16 44 H34 V118 H16 Z" fill="#2F241B" strokeWidth="1.4" />
        <path d="M114 44 H132 V118 H114 Z" fill="#2F241B" strokeWidth="1.4" />
        {/* braces */}
        <path d="M34 44 L52 62 M114 44 L96 62" strokeWidth="1.2" opacity="0.9" />
        {/* wood grain on the beam */}
        <path d="M14 34 H134 M14 39 H134" strokeWidth="0.8" opacity="0.5" />
        {/* nails */}
      </g>
      <g fill="#7B6E5E">
        <circle cx="24" cy="37" r="1.4" />
        <circle cx="124" cy="37" r="1.4" />
        <circle cx="25" cy="60" r="1.2" />
        <circle cx="123" cy="60" r="1.2" />
      </g>

      {/* the lamp, hanging from the beam into the shaft */}
      <g>
        <path d="M74 44 V56" stroke="#6B5539" strokeWidth="1" />
        <path d="M67 56 H81 L78 66 H70 Z" fill="#B0752E" stroke="#0E0B09" strokeWidth="1" />
        <circle cx="74" cy="68" r="3.4" fill="#F2B65A" />
        <circle cx="74" cy="68" r="9" fill="#F2B65A" opacity="0.14" />
        <path d="M64 84 L84 84 L96 118 H52 Z" fill="#F2B65A" opacity="0.05" />
      </g>

      {/* the mouth of the shaft, a dark lip */}
      <path d="M30 34 H118" stroke="#0E0B09" strokeWidth="3" />
    </svg>
  );
}
