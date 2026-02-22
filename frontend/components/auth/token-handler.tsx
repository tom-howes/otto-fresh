"use client";
import { useEffect } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";

const TokenHandler = () => {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const token = searchParams.get("token");
    if (token) {
      document.cookie = `session_token=${token}; path=/; max-age=${7 * 24 * 60 * 60}; SameSite=Lax`;
      // Clean the token out of the URL without a page reload
      router.replace(pathname);
    }
  }, []);

  return null;
};

export default TokenHandler;