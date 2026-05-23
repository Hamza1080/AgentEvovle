import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

function normalizeInput(body: any) {
  if (!body) throw new Error("Empty request body");

  const dateRange = body.dateRange || {};

  const from = dateRange.from ? new Date(dateRange.from) : null;
  const to = dateRange.to ? new Date(dateRange.to) : null;

  const getDays = () => {
    if (!from || !to || isNaN(from.getTime()) || isNaN(to.getTime())) {
      return 3; // default trip length (important for EvoAgent stability)
    }

    return Math.max(
      1,
      Math.ceil((to.getTime() - from.getTime()) / (1000 * 60 * 60 * 24)) + 1
    );
  };

  const formatDate = (d: any) =>
    d ? new Date(d).toISOString().split("T")[0] : null;

  return {
    // ✅ REQUIRED FIELDS (never undefined)
    org: body.origin?.trim() || "Unknown Origin",
    dest: body.destination?.trim() || "Unknown Destination",

    query: body.query?.trim() || "",

    // ✅ deterministic fallback
    days: getDays(),

    date: [
      formatDate(dateRange.from),
      formatDate(dateRange.to),
    ],

    // ✅ safe numeric defaults (NEVER null for pipeline stability)
    people_number: body.travelers ? Number(body.travelers) : 1,
    budget: body.budget ? Number(body.budget) : 1000,

    local_constraint: {
      "house rule": body.houseRules || [],
      cuisine: body.cuisines || [],
      "room type": body.roomType || "standard",
      transportation: null,
    },

    level: "easy",
  };
}

export async function POST(req: Request) {
  try {
    const body = await req.json();

    console.log("📥 RAW INPUT RECEIVED:", body);

    const normalized = normalizeInput(body);

    // ensure /data exists
    const dir = path.join(process.cwd(), "data");
    fs.mkdirSync(dir, { recursive: true });

    const filePath = path.join(dir, "input.json");

    // IMPORTANT: single object (NOT array) → avoids Python confusion
    fs.writeFileSync(
      filePath,
      JSON.stringify(normalized, null, 2)
    );

    console.log("💾 input.json SAVED:", normalized);

    return NextResponse.json({
      success: true,
      normalized,
    });

  } catch (err: any) {
    console.error("❌ PLAN ERROR:", err);

    return NextResponse.json(
      { success: false, error: err.message },
      { status: 500 }
    );
  }
}