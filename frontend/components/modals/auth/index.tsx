"use client";
import {
  Modal,
  ModalClose,
  ModalContent,
  ModalOverlay,
  ModalPortal,
} from "@/components/ui/modal";
import { useAuthModalContext } from "@/context/use-auth-modal";
import { SignIn } from "@/components/modals/auth/MockAuth"; // Update the path to the correct file location
import { usePathname } from "next/navigation";
import { useEffect } from "react";
import { MdClose } from "react-icons/md";

const AuthModal = () => {
  const { authModalIsOpen, setAuthModalIsOpen } = useAuthModalContext();
  const pathname = usePathname();

  useEffect(() => {
    if (pathname === "/sign-up") {
      setAuthModalIsOpen(false);
    }
  }, [pathname, setAuthModalIsOpen]);

  return (
    <Modal open={authModalIsOpen} onOpenChange={setAuthModalIsOpen}>
      <ModalPortal>
        <ModalOverlay />
        <ModalContent
          customStyle
          className="top-1/2 h-fit w-fit -translate-y-1/2 overflow-hidden"
        >
          <ModalClose className="absolute right-10 top-5 z-50">
            <MdClose />
          </ModalClose>
          <SignIn />
        </ModalContent>
      </ModalPortal>
    </Modal>
  );
};

export { AuthModal };
