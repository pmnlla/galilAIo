"use client"
import useSWR from 'swr'

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export default function VideoPlayer() {
  const { data, error, isLoading } = useSWR('http://localhost:8000/latest', fetcher)

  if (error) return <div>Failed to load</div>
  if (isLoading) return <div>Loading...</div>

  return (
    <div>
      {data?.url && (
        <video src={data.url} controls />
      )}
    </div>
  )
}
