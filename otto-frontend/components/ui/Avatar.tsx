"use client";

const AVATAR_COLORS = [
  "bg-violet-500",
  "bg-teal-500",
  "bg-blue-500",
  "bg-orange-500",
  "bg-pink-500",
];

interface AvatarProps {
  letter: string;
  size?: "sm" | "lg";
}

export default function Avatar({ letter, size = "sm" }: AvatarProps) {
  const safeStr = typeof letter === "string" ? letter : "";
  const isUnassigned = !safeStr || safeStr === "?";
  const colorClass = isUnassigned
    ? "bg-gray-100 dark:bg-gray-800 border border-dashed border-gray-300 dark:border-gray-600"
    : AVATAR_COLORS[safeStr.charCodeAt(0) % AVATAR_COLORS.length];
  return (
    <div
      className={`${colorClass} ${
        size === "lg" ? "h-8 w-8" : "h-6 w-6"
      } flex items-center justify-center rounded-full font-bold shrink-0 ${
        isUnassigned ? "text-gray-400 dark:text-gray-500" : "text-white text-xs"
      }`}
    >
      {isUnassigned ? (
        <svg className={size === "lg" ? "h-4 w-4" : "h-3 w-3"} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
        </svg>
      ) : safeStr[0]}
    </div>
  );
}