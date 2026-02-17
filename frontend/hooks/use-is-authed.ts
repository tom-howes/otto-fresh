"use client";
import { useAuthModalContext } from "@/context/use-auth-modal";
import { useAuth } from "@/context/use-auth-context";

export const useIsAuthenticated = (): [string | undefined, () => void] => {
  const { user, isAuthenticated } = useAuth();
  const { setAuthModalIsOpen } = useAuthModalContext();

  function openAuthModal() {
    setAuthModalIsOpen(true);
  }

  return [isAuthenticated ? user?.id : undefined, openAuthModal];
};