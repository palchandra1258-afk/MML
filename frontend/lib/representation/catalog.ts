/**
 * Versioned frontend snapshot copied from the backend representation taxonomy
 * and default availability registry. There is no API endpoint for these
 * definitions; the UI labels them as repository defaults, not runtime data.
 */
export const taxonomyVersion = "1.0";

export const representationTaxonomy = [
  { representation_id: "textual", label: "Textual representation", examples: ["simplified explanation", "concept definition", "alternative wording", "short summary"], configuration_fields: ["explanation_complexity", "required_content"] },
  { representation_id: "worked_example", label: "Worked example", examples: ["step-by-step solution", "solved problem", "worked example followed by similar practice"], configuration_fields: ["example_count", "difficulty_level", "required_content"] },
  { representation_id: "visual", label: "Visual representation", examples: ["concept diagram", "flow diagram", "graph", "annotated illustration", "visual comparison"], configuration_fields: ["visual_detail_level", "required_content"] },
  { representation_id: "symbolic", label: "Symbolic representation", examples: ["equation", "formula decomposition", "symbol manipulation", "algebraic transformations"], configuration_fields: ["explanation_complexity", "required_content"] },
  { representation_id: "interactive", label: "Interactive representation", examples: ["interactive graph", "parameter adjustment", "visual manipulation", "exploratory activity"], configuration_fields: ["interaction_type", "difficulty_level", "required_content"] },
  { representation_id: "simulation", label: "Simulation", examples: ["parameter-based simulation", "dynamic visualization", "what-if exploration"], configuration_fields: ["interaction_type", "difficulty_level", "required_content"] },
  { representation_id: "diagnostic", label: "Diagnostic representation", examples: ["diagnostic question", "conceptual assessment", "reasoning prompt", "intermediate-step request"], configuration_fields: ["difficulty_level", "required_content"] },
  { representation_id: "alternative_explanation", label: "Alternative or continued explanation", examples: ["continue current explanation", "simpler wording", "change explanation strategy", "different example"], configuration_fields: ["explanation_complexity", "example_count", "required_content"] },
] as const;

export const defaultCapabilityRegistry = representationTaxonomy.map(({ representation_id }) => ({
  representation_id,
  status: "unavailable" as const,
  provider_id: null,
  content_ids: [] as string[],
  reason: "No representation delivery provider or concept-grounded content source is implemented in this repository.",
}));

export type RepresentationDefinition = (typeof representationTaxonomy)[number];
export type DefaultCapability = (typeof defaultCapabilityRegistry)[number];
