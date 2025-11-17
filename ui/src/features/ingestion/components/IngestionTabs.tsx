import { FormEvent, useState } from "react";
import { Corpus } from "../../../lib/api/types";
import { Button } from "../../../components/ui/button";
import { Input } from "../../../components/ui/input";
import { Textarea } from "../../../components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../../components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../../components/ui/tabs";

type Props = {
  corpora: Corpus[];
  onIngestText: (args: { corpus_id: string; text: string }) => Promise<void> | void;
  onIngestUrl: (args: { corpus_id: string; url: string }) => Promise<void> | void;
  onIngestFile?: (args: { corpus_id: string; file: File }) => Promise<void> | void;
  isSubmitting?: boolean;
  resultMessage?: string;
  errorMessage?: string;
};

export function IngestionTabs({
  corpora,
  onIngestText,
  onIngestUrl,
  onIngestFile,
  isSubmitting,
  resultMessage,
  errorMessage
}: Props) {
  const [corpusId, setCorpusId] = useState(corpora[0]?.id ?? "");
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");

  const targetCorpus =
    corpora.find((c) => c.id === corpusId)?.name ?? (corpora.length ? corpora[0].name : "No corpora");

  async function handleText(e: FormEvent) {
    e.preventDefault();
    await onIngestText({ corpus_id: corpusId, text });
    setText("");
  }

  async function handleUrl(e: FormEvent) {
    e.preventDefault();
    await onIngestUrl({ corpus_id: corpusId, url });
    setUrl("");
  }

  async function handleFile(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const files = (e.currentTarget.elements.namedItem("file") as HTMLInputElement | null)?.files;
    const file = files?.[0];
    if (file && onIngestFile) {
      await onIngestFile({ corpus_id: corpusId, file });
      (e.currentTarget.elements.namedItem("file") as HTMLInputElement).value = "";
    }
  }

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex items-center justify-between gap-4">
        <div className="text-sm font-medium">Target corpus</div>
        <Select value={corpusId} onValueChange={setCorpusId}>
          <SelectTrigger className="w-[300px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {corpora.map((c) => (
              <SelectItem key={c.id} value={c.id}>
                {c.name} ({c.type})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Tabs defaultValue="text" className="mt-4">
        <TabsList>
          <TabsTrigger value="text">TEXT</TabsTrigger>
          <TabsTrigger value="url">URL</TabsTrigger>
          <TabsTrigger value="file">FILE</TabsTrigger>
        </TabsList>

        <TabsContent value="text">
          <form className="mt-4 flex flex-col gap-3" onSubmit={handleText}>
            <div className="space-y-2">
              <label htmlFor="ingest-text" className="text-sm font-medium">
                Text to ingest
              </label>
              <Textarea
                id="ingest-text"
                rows={6}
                value={text}
                onChange={(e) => setText(e.target.value)}
                required
              />
            </div>
            <Button type="submit" disabled={isSubmitting} className="w-fit">
              {isSubmitting ? "Ingesting…" : `Ingest to ${targetCorpus}`}
            </Button>
          </form>
        </TabsContent>

        <TabsContent value="url">
          <form className="mt-4 flex flex-col gap-3" onSubmit={handleUrl}>
            <div className="space-y-2">
              <label htmlFor="ingest-url" className="text-sm font-medium">
                URL
              </label>
              <Input
                id="ingest-url"
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                required
                placeholder="https://example.com/article"
              />
            </div>
            <Button type="submit" disabled={isSubmitting} className="w-fit">
              {isSubmitting ? "Ingesting…" : `Fetch & ingest to ${targetCorpus}`}
            </Button>
          </form>
        </TabsContent>

        <TabsContent value="file">
          <form className="mt-4 flex flex-col gap-3" onSubmit={handleFile}>
            <div className="space-y-2">
              <label htmlFor="ingest-file" className="text-sm font-medium">
                File
              </label>
              <Input
                id="ingest-file"
                type="file"
                name="file"
                required
                accept=".txt,.md,.pdf"
              />
            </div>
            <Button
              type="submit"
              disabled={isSubmitting || !onIngestFile}
              className="w-fit"
              title={onIngestFile ? undefined : "File ingest not yet wired"}
            >
              {isSubmitting ? "Uploading…" : `Upload to ${targetCorpus}`}
            </Button>
          </form>
        </TabsContent>
      </Tabs>

      {resultMessage && <div className="mt-3 text-sm text-foreground">{resultMessage}</div>}
      {errorMessage && <div className="mt-2 text-sm text-destructive">{errorMessage}</div>}
    </div>
  );
}

export default IngestionTabs;
