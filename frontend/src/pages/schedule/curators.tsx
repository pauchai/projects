import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useCurators, useCreateCurator, useAddAvailabilitySlot } from "@/hooks/use-schedule"
import type { CuratorResponse } from "@/api/types"

const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

function CuratorCard({ curator }: { curator: CuratorResponse }) {
  const [showSlotForm, setShowSlotForm] = useState(false)
  const [weekday, setWeekday] = useState(0)
  const [startTime, setStartTime] = useState("09:00")
  const [endTime, setEndTime] = useState("11:00")
  const addSlot = useAddAvailabilitySlot(curator.curator_id)

  function handleAddSlot(e: React.FormEvent) {
    e.preventDefault()
    addSlot.mutate(
      { weekday, start_time: startTime, end_time: endTime },
      { onSuccess: () => setShowSlotForm(false) },
    )
  }

  return (
    <div className="rounded-lg border p-4 shadow-sm">
      <h3 className="text-lg font-semibold">{curator.name}</h3>

      {curator.skills.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {curator.skills.map((skill) => (
            <span
              key={skill}
              className="rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-800"
            >
              {skill}
            </span>
          ))}
        </div>
      )}

      {curator.availability_slots.length > 0 && (
        <div className="mt-3">
          <p className="text-sm font-medium text-gray-600">Availability</p>
          <ul className="mt-1 space-y-0.5">
            {curator.availability_slots.map((slot) => (
              <li key={slot.slot_id} className="text-sm text-gray-700">
                {WEEKDAYS[slot.weekday]} {slot.start_time}–{slot.end_time}
              </li>
            ))}
          </ul>
        </div>
      )}

      <Button
        variant="outline"
        size="sm"
        className="mt-3"
        onClick={() => setShowSlotForm((v) => !v)}
      >
        {showSlotForm ? "Cancel" : "+ Add slot"}
      </Button>

      {showSlotForm && (
        <form onSubmit={handleAddSlot} className="mt-3 flex flex-wrap items-end gap-2">
          <div>
            <label className="block text-xs text-gray-500">Day</label>
            <select
              className="rounded border px-2 py-1 text-sm bg-background text-foreground"
              value={weekday}
              onChange={(e) => setWeekday(Number(e.target.value))}
            >
              {WEEKDAYS.map((d, i) => (
                <option key={d} value={i}>
                  {d}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500">From</label>
            <Input
              type="time"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              className="w-28 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500">To</label>
            <Input
              type="time"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              className="w-28 text-sm"
            />
          </div>
          <Button type="submit" size="sm" disabled={addSlot.isPending}>
            {addSlot.isPending ? "Saving..." : "Save"}
          </Button>
          {addSlot.isError && (
            <p className="w-full text-xs text-red-600">{String(addSlot.error)}</p>
          )}
        </form>
      )}
    </div>
  )
}

export function CuratorsPage() {
  const { data: curators, isLoading, isError } = useCurators()
  const createCurator = useCreateCurator()

  const [name, setName] = useState("")
  const [skills, setSkills] = useState("")
  const [showForm, setShowForm] = useState(false)

  function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    const skillList = skills
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean)
    createCurator.mutate(
      { name, skills: skillList },
      {
        onSuccess: () => {
          setName("")
          setSkills("")
          setShowForm(false)
        },
      },
    )
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Curators</h1>
        <Button onClick={() => setShowForm((v) => !v)}>
          {showForm ? "Cancel" : "New curator"}
        </Button>
      </div>

      {showForm && (
        <form
          onSubmit={handleCreate}
          className="mb-6 flex flex-col gap-3 rounded-lg border p-4 sm:flex-row sm:items-end"
        >
          <div className="flex-1">
            <label className="block text-sm font-medium">Name</label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Curator name"
              required
            />
          </div>
          <div className="flex-1">
            <label className="block text-sm font-medium">Skills (comma-separated)</label>
            <Input
              value={skills}
              onChange={(e) => setSkills(e.target.value)}
              placeholder="Python, Math, English"
            />
          </div>
          <Button type="submit" disabled={createCurator.isPending}>
            {createCurator.isPending ? "Creating..." : "Create"}
          </Button>
          {createCurator.isError && (
            <p className="text-xs text-red-600">{String(createCurator.error)}</p>
          )}
        </form>
      )}

      {isLoading && <p className="text-gray-500">Loading...</p>}
      {isError && <p className="text-red-600">Failed to load curators.</p>}

      {curators && curators.length === 0 && (
        <p className="text-gray-500">No curators yet.</p>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {curators?.map((curator) => (
          <CuratorCard key={curator.curator_id} curator={curator} />
        ))}
      </div>
    </div>
  )
}
