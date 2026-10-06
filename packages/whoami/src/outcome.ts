import { InputError } from "./input.js";

export type ContextErrorOutcome = {
  schema: "whoami.error.v1";
  status: "error";
  command: "context";
  years: number[];
  code: string;
  message: string;
};

export function contextErrorOutcome(
  error: InputError,
  years: number[],
): ContextErrorOutcome {
  return {
    schema: "whoami.error.v1",
    status: "error",
    command: "context",
    years: [...years],
    code: error.code,
    message: error.message,
  };
}
