declare module "node:path" {
  export function resolve(...paths: string[]): string;
}

declare module "node:fs" {
  export function readFileSync(path: string, encoding: string): string;
}

declare module "node:url" {
  export function fileURLToPath(url: string | URL): string;
}

interface ImportMeta {
  url: string;
}

interface URL {
  protocol: string;
  host: string;
  pathname: string;
  search: string;
}

declare const URL: {
  prototype: URL;
  new(input: string, base?: string | URL): URL;
};

declare const process: {
  env: Record<string, string | undefined>;
};
