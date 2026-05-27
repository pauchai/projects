import { create } from "zustand"
import { persist } from "zustand/middleware"

interface CommunityState {
  selectedCommunityId: string | null
  setSelectedCommunity: (id: string | null) => void
}

export const useCommunityStore = create<CommunityState>()(
  persist(
    (set) => ({
      selectedCommunityId: null,
      setSelectedCommunity: (id) => set({ selectedCommunityId: id }),
    }),
    { name: "community-storage" },
  ),
)
