import katex from "katex";
export function Formula({ value }: { value: string }) {
  return (
    <div
      className="formula"
      dangerouslySetInnerHTML={{
        __html: katex.renderToString(value, {
          throwOnError: false,
          displayMode: true,
          trust: false,
        }),
      }}
    />
  );
}
