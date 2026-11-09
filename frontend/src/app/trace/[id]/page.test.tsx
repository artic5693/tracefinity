// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import TracePage from './page'

window.matchMedia = vi.fn().mockReturnValue({
  matches: false,
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
}) as unknown as typeof window.matchMedia

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({ id: 'sess-local-1' }),
}))

vi.mock('@/components/PaperCornerEditor', () => ({
  PaperCornerEditor: () => <div data-testid="corner-editor" />,
}))

vi.mock('@/components/PolygonEditor', () => ({
  PolygonEditor: () => <div data-testid="polygon-editor" />,
}))

vi.mock('@/lib/api', () => ({
  getSession: vi.fn(),
  getAvailableKeys: vi.fn(),
  setCorners: vi.fn(),
  traceTools: vi.fn(),
  traceFromMask: vi.fn(),
  updatePolygons: vi.fn(),
  updateSession: vi.fn(),
  getImageUrl: (path: string) => path,
  saveToolsFromSession: vi.fn(),
}))

import { getAvailableKeys, getSession, setCorners, traceTools } from '@/lib/api'

const getSessionMock = vi.mocked(getSession)
const getAvailableKeysMock = vi.mocked(getAvailableKeys)
const setCornersMock = vi.mocked(setCorners)
const traceToolsMock = vi.mocked(traceTools)

beforeEach(() => {
  getSessionMock.mockReset()
  getAvailableKeysMock.mockReset()
  setCornersMock.mockReset()
  traceToolsMock.mockReset()
})

afterEach(() => {
  cleanup()
})

import type { Polygon, Session } from '@/types'

const SAMPLE_POLYGON: Polygon = {
  id: 'p1',
  label: 'tool 1',
  points: [{ x: 10, y: 10 }, { x: 20, y: 10 }, { x: 20, y: 20 }],
  interior_rings: [],
  finger_holes: [],
}

function makeSession(overrides: Partial<Session> = {}): Session {
  return {
    id: 'sess-local-1',
    name: null,
    description: null,
    tags: [],
    created_at: '2026-11-04T00:00:00Z',
    original_image_path: null,
    corrected_image_path: 'default/processed/sess-local-1.jpg',
    corners: [
      { x: 0, y: 0 },
      { x: 100, y: 0 },
      { x: 100, y: 100 },
      { x: 0, y: 100 },
    ],
    paper_size: 'a4',
    scale_factor: 0.2,
    focal_length_35mm: null,
    photo_warnings: null,
    polygons: [],
    mask_image_path: null,
    stl_path: null,
    layout: null,
    ...overrides,
  }
}

describe('TracePage local model & manual mask workflow', () => {
  it('allows switching to Manual mask upload and back when only local tracers are configured', async () => {
    getSessionMock.mockResolvedValue(makeSession())

    getAvailableKeysMock.mockResolvedValue({
      google: true,
      provider: 'local',
      provider_label: 'InSPyReNet',
      tracers: [
        { id: 'inspyrenet', label: 'InSPyReNet' },
        { id: 'birefnet-lite', label: 'BiRefNet Lite' },
        { id: 'isnet', label: 'IS-Net' },
      ],
      photo_stations: false,
    })

    render(<TracePage />)

    // Default local tracer is selected on the trace step
    expect(await screen.findByText('InSPyReNet')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Trace Tools' })).toBeTruthy()

    // Click "Upload a mask manually" link
    fireEvent.click(screen.getByRole('button', { name: 'Upload a mask manually' }))

    // Manual upload controls and prompt are shown
    expect(await screen.findByRole('button', { name: 'Download Image' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Upload Mask' })).toBeTruthy()
    expect(screen.getByText(/Trace the actual edges of each object, NOT the shadow edges/)).toBeTruthy()

    // Open the Tracer dropdown to switch back to BiRefNet Lite
    fireEvent.click(screen.getByRole('button', { name: 'Manual mask upload' }))
    fireEvent.click(screen.getByRole('button', { name: 'BiRefNet Lite' }))

    traceToolsMock.mockResolvedValue({
      polygons: [SAMPLE_POLYGON],
      mask_url: '/storage/default/processed/sess-local-1_mask.png',
    })

    fireEvent.click(screen.getByRole('button', { name: 'Trace Tools' }))
    await waitFor(() => {
      expect(traceToolsMock).toHaveBeenCalledWith('sess-local-1', 'google', undefined, 'birefnet-lite')
    })
  })

  it('keeps Trace Tools and Manual mask upload accessible on Re-trace even with a single local tracer', async () => {
    getSessionMock.mockResolvedValue(makeSession({
      polygons: [SAMPLE_POLYGON],
      mask_image_path: 'default/processed/sess-local-1_mask.png',
    }))

    getAvailableKeysMock.mockResolvedValue({
      google: true,
      provider: 'local',
      provider_label: 'IS-Net',
      tracers: [{ id: 'isnet', label: 'IS-Net' }],
      photo_stations: false,
    })

    render(<TracePage />)

    // Starts on edit step since polygons exist; click Re-trace
    fireEvent.click(await screen.findByRole('button', { name: 'Re-trace' }))

    // Both Trace Tools and Upload a mask manually are available
    expect(await screen.findByRole('button', { name: 'Trace Tools' })).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Upload a mask manually' }))
    expect(await screen.findByRole('button', { name: 'Upload Mask' })).toBeTruthy()
  })

  it('auto-traces with primary tracer on Continue when multiple local tracers are configured', async () => {
    getSessionMock.mockResolvedValue(makeSession({
      corrected_image_path: null,
      polygons: [],
    }))

    getAvailableKeysMock.mockResolvedValue({
      google: true,
      provider: 'local',
      provider_label: 'InSPyReNet',
      tracers: [
        { id: 'inspyrenet', label: 'InSPyReNet' },
        { id: 'birefnet-lite', label: 'BiRefNet Lite' },
        { id: 'isnet', label: 'IS-Net' },
      ],
      photo_stations: false,
    })

    setCornersMock.mockResolvedValue({
      corrected_image_url: '/storage/default/processed/sess-local-1_corrected.jpg',
      scale_factor: 0.2,
      warnings: [],
    })

    traceToolsMock.mockResolvedValue({
      polygons: [SAMPLE_POLYGON],
      mask_url: '/storage/default/processed/sess-local-1_mask.png',
    })

    render(<TracePage />)

    // Click Continue on the Corners step
    fireEvent.click(await screen.findByRole('button', { name: 'Continue' }))

    await waitFor(() => {
      expect(setCornersMock).toHaveBeenCalledTimes(1)
      expect(traceToolsMock).toHaveBeenCalledWith('sess-local-1', 'google', undefined, 'inspyrenet')
    })

    // Lands directly on the Select Tools (edit) step
    expect(await screen.findByRole('button', { name: 'Re-trace' })).toBeTruthy()
  })
})
