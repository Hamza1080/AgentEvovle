import { NextResponse } from "next/server";
import { runModelPipeline } from "@/lib/runModel";

export async function GET() {
  runModelPipeline();

  return NextResponse.json({
    success: true,
    message: "Model executed, output.json created"
  });
}