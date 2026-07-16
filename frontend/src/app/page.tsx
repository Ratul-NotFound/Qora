import Sidebar from "@/components/Sidebar";
import SearchBox from "@/components/SearchBox";

export default function Home() {
  return (
    <div className="flex w-full min-h-screen">
      <Sidebar />
      <main className="flex-1 p-8 overflow-y-auto">
        <header className="mb-12 mt-8">
          <h1 className="text-5xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
            Autonomous Research Intelligence
          </h1>
          <p className="text-slate-400 text-lg">
            Enter a topic. QORA will search, read, analyze, and synthesize the global state of the art.
          </p>
        </header>

        <section className="max-w-3xl glass-panel p-8 rounded-3xl">
          <SearchBox />
        </section>
      </main>
    </div>
  );
}
