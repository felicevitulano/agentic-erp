interface PlaceholderPageProps {
  title: string
  description: string
}

export default function PlaceholderPage({ title, description }: PlaceholderPageProps) {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">{title}</h1>
      <div className="card">
        <p className="text-gray-500">{description}</p>
        <p className="text-sm text-gray-400 mt-2">Usa l'assistente AI per interagire con questo modulo.</p>
      </div>
    </div>
  )
}
