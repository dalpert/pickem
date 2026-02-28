import Image from "next/image";

interface AvatarProps {
  name: string;
  avatarFilename: string | null;
  color?: string;
  size?: "sm" | "md" | "lg";
}

const SIZES = { sm: 24, md: 30, lg: 64 };

export default function Avatar({
  name,
  avatarFilename,
  color = "#4a7c96",
  size = "md",
}: AvatarProps) {
  const px = SIZES[size];
  const cls = size === "sm" ? "avatar avatar-sm" : size === "lg" ? "avatar avatar-lg" : "avatar";

  if (avatarFilename) {
    return (
      <Image
        className={cls}
        src={`/avatars/${avatarFilename}`}
        alt={name}
        width={px}
        height={px}
      />
    );
  }

  return (
    <span
      className={`avatar-placeholder`}
      style={{ background: color, width: px, height: px, fontSize: px * 0.4 }}
    >
      {name[0]?.toUpperCase() ?? "?"}
    </span>
  );
}
