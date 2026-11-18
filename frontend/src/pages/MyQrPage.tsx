import { useEffect, useState, type FormEvent } from 'react'
import { QrCode } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { getErrorMessage } from '../lib/api'
import { deactivateQr, getMyQr, registerQr } from '../lib/resources'
import type { QrRegistration } from '../types'

export function MyQrPage() {
  const [items, setItems] = useState<QrRegistration[]>([])
  const [itemName, setItemName] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  function load() {
    getMyQr()
      .then(setItems)
      .catch(() => setItems([]))
  }

  useEffect(() => {
    load()
  }, [])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await registerQr(itemName, description)
      setItemName('')
      setDescription('')
      load()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDeactivate(id: number) {
    await deactivateQr(id)
    load()
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="text-2xl font-bold text-midnight">QR Codes</h1>
      <p className="text-sm text-midnight/60">
        Register your belongings so a finder can notify you privately.
      </p>

      <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-3 rounded-2xl border border-midnight/10 bg-white p-5">
        {error && <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
        <Input
          id="item_name"
          label="Item name"
          value={itemName}
          onChange={(e) => setItemName(e.target.value)}
          required
        />
        <Input
          id="description"
          label="Description (optional)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
        <Button type="submit" disabled={submitting}>
          <QrCode className="h-4 w-4" /> Register item
        </Button>
      </form>

      {items.length > 0 && (
        <ul className="mt-6 flex flex-col gap-3">
          {items.map((item) => (
            <li key={item.id} className="rounded-2xl border border-midnight/10 bg-white p-5">
              <div className="flex items-center justify-between">
                <p className="font-semibold text-midnight">{item.item_name}</p>
                <QrCode className="h-5 w-5 text-brand" />
              </div>
              {item.description && (
                <p className="mt-1 text-sm text-midnight/60">{item.description}</p>
              )}
              {item.qr_url && (
                <p className="mt-2 text-xs text-midnight/50">
                  Recovery link:{' '}
                  <span className="font-mono text-brand">{item.qr_url}</span>
                </p>
              )}
              {item.is_active ? (
                <Button variant="ghost" className="mt-3" onClick={() => handleDeactivate(item.id)}>
                  Deactivate
                </Button>
              ) : (
                <p className="mt-3 text-xs font-medium uppercase text-midnight/40">Inactive</p>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
