import { createContext, useContext } from "react";

// Lets page components remain compatible while the router owns one persistent shell.
export const LayoutContext = createContext(false);

export function useAppShell() {
  return useContext(LayoutContext);
}
