import React from 'react';

interface SlothMascotProps {
  className?: string;
  size?: number;
}

export const SlothMascot: React.FC<SlothMascotProps> = ({ className = '', size = 36 }) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`inline-block ${className}`}
      aria-label="SlothSort Mascot"
    >
      {/* Branch */}
      <path
        d="M2 34C14 34 22 36 46 32"
        stroke="#8D6E63"
        strokeWidth="4"
        strokeLinecap="round"
      />
      {/* Leaf on branch */}
      <path
        d="M38 31C39 27 44 26 44 26C44 26 43 31 38 31Z"
        fill="#52B788"
      />

      {/* Sloth body hanging */}
      <ellipse
        cx="24"
        cy="26"
        rx="14"
        ry="10"
        fill="#A1887F"
      />

      {/* Sloth Face */}
      <circle
        cx="14"
        cy="25"
        r="7.5"
        fill="#D7CCC8"
      />

      {/* Eye patches */}
      <path
        d="M9 24C10 21 14 22 14 24C14 25.5 11 26 9 24Z"
        fill="#6D4C41"
      />
      <path
        d="M15 24C16 21 20 22 20 24C20 25.5 17 26 15 24Z"
        fill="#6D4C41"
      />

      {/* Calm, contented eyes (relaxed horizontal curves) */}
      <path
        d="M10.5 24C11.5 25 12.5 25 13.5 24"
        stroke="#2D6A4F"
        strokeWidth="1.2"
        strokeLinecap="round"
      />
      <path
        d="M16.5 24C17.5 25 18.5 25 19.5 24"
        stroke="#2D6A4F"
        strokeWidth="1.2"
        strokeLinecap="round"
      />

      {/* Cute nose */}
      <ellipse
        cx="14"
        cy="27"
        rx="1.5"
        ry="1"
        fill="#3E2723"
      />

      {/* Relaxed smile */}
      <path
        d="M13 29C13.8 30 14.5 30 15.2 29"
        stroke="#3E2723"
        strokeWidth="1"
        strokeLinecap="round"
      />

      {/* Hanging arms gripping branch */}
      <path
        d="M18 20C18 17 21 17 21 20"
        stroke="#8D6E63"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      <path
        d="M28 20C28 17 31 17 31 20"
        stroke="#8D6E63"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
    </svg>
  );
};
