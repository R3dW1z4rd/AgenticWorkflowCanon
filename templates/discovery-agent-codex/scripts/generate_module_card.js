#!/usr/bin/env node
/**
 * generate_module_card.js
 * -----------------------
 * Reads a 01-module-*.md file and generates a formatted .docx Module Definition Card.
 *
 * Usage:
 *   node scripts/generate_module_card.js <path-to-module-md> <output-path>
 *
 * Example:
 *   node scripts/generate_module_card.js workspace/contract-manager/01-module-contract-creation.md \
 *        workspace/contract-manager/exports/module-card-contract-creation.docx
 */

const fs   = require('fs');
const path = require('path');

// Try global docx install
let docxPath = '/home/claude/.npm-global/lib/node_modules/docx';
if (!fs.existsSync(docxPath)) docxPath = 'docx'; // fallback to local

const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, BorderStyle, WidthType, ShadingType,
  VerticalAlign
} = require(docxPath);

// ── Args ──────────────────────────────────────────────────────────────────────
const [,, mdPath, outPath] = process.argv;
if (!mdPath || !outPath) {
  console.error('Usage: node generate_module_card.js <module.md> <output.docx>');
  process.exit(1);
}

const mdText = fs.existsSync(mdPath) ? fs.readFileSync(mdPath, 'utf8') : '';
const slug   = path.basename(mdPath, '.md').replace('01-module-', '');
const title  = slug.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

// ── Colors ────────────────────────────────────────────────────────────────────
const BRAND_BLUE = '1F4E79';
const MID_BLUE   = '2E75B6';
const LIGHT_BLUE = 'D6E4F0';
const LIGHT_GREY = 'F2F2F2';
const MID_GREY   = '888888';
const WHITE      = 'FFFFFF';

// ── Extract section from markdown ─────────────────────────────────────────────
function extractSection(md, heading) {
  const re = new RegExp(
    `##\\s+\\d*\\.?\\s*${heading}.*?\\n([\\s\\S]*?)(?=\\n##|$)`, 'i'
  );
  const m = md.match(re);
  return m ? m[1].trim() : '';
}

function extractMeta(md, field) {
  const re = new RegExp(`\\*\\*${field}:\\*\\*\\s*(.+)`, 'i');
  const m  = md.match(re);
  return m ? m[1].trim() : '';
}

// ── Helpers ───────────────────────────────────────────────────────────────────
const CONTENT_W = 9360;
const cellPad   = { top: 100, bottom: 100, left: 150, right: 150 };

const borderDef = (color = 'BFBFBF') => ({
  style: BorderStyle.SINGLE, size: 4, color
});
const allBorders = (color = 'BFBFBF') => ({
  top: borderDef(color), bottom: borderDef(color),
  left: borderDef(color), right: borderDef(color)
});
const noBorders = () => {
  const n = { style: BorderStyle.NONE, size: 0, color: WHITE };
  return { top: n, bottom: n, left: n, right: n };
};

function sectionHeaderPara(text) {
  return new Paragraph({
    spacing: { before: 240, after: 80 },
    shading: { fill: BRAND_BLUE, type: ShadingType.CLEAR, color: BRAND_BLUE },
    children: [new TextRun({
      text: `  ${text}`, bold: true, size: 22, color: WHITE, font: 'Arial'
    })]
  });
}

function contentPara(text, hint = false) {
  return new Paragraph({
    spacing: { before: 60, after: 60 },
    children: [new TextRun({
      text: text || (hint ? '—' : ''),
      size: 20,
      color: hint ? MID_GREY : '333333',
      italics: hint,
      font: 'Arial'
    })]
  });
}

function spacer(before = 80, after = 80) {
  return new Paragraph({ spacing: { before, after }, children: [] });
}

// ── Meta 2-column table ───────────────────────────────────────────────────────
function metaTable(items) {
  const colW = CONTENT_W / 2;
  const rows = [];
  for (let i = 0; i < items.length; i += 2) {
    const pair = items.slice(i, i + 2);
    while (pair.length < 2) pair.push(['', '']);
    rows.push(new TableRow({
      children: pair.map(([lbl, val]) =>
        new TableCell({
          width: { size: colW, type: WidthType.DXA },
          borders: allBorders(LIGHT_BLUE),
          shading: { fill: LIGHT_BLUE, type: ShadingType.CLEAR },
          margins: cellPad,
          children: [new Paragraph({
            children: [
              new TextRun({ text: `${lbl}: `, bold: true, size: 20, font: 'Arial', color: BRAND_BLUE }),
              new TextRun({ text: val || '', size: 20, font: 'Arial', color: '444444' })
            ]
          })]
        })
      )
    }));
  }
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [colW, colW],
    rows
  });
}

// ── Actors table ──────────────────────────────────────────────────────────────
function actorsTable(content) {
  const cols = [2200, 3000, 2560, 1600];
  const headers = ['Role', 'Actions', 'What they see', 'Notes'];

  const headerRow = new TableRow({
    children: headers.map((h, i) => new TableCell({
      width: { size: cols[i], type: WidthType.DXA },
      borders: allBorders(MID_BLUE),
      shading: { fill: MID_BLUE, type: ShadingType.CLEAR },
      margins: cellPad,
      children: [new Paragraph({
        children: [new TextRun({ text: h, bold: true, size: 20, color: WHITE, font: 'Arial' })]
      })]
    }))
  });

  // Parse markdown table rows from content
  const dataRows = content.split('\n')
    .filter(l => l.trim().startsWith('|') && !l.match(/^\|[\s\-:|]+\|/))
    .slice(1) // skip header
    .map(l => l.trim().replace(/^\||\|$/g, '').split('|').map(c => c.trim()));

  const bodyRows = (dataRows.length > 0 ? dataRows : [['', '', '', '']]).map((row, ri) =>
    new TableRow({
      children: cols.map((w, ci) => new TableCell({
        width: { size: w, type: WidthType.DXA },
        borders: allBorders(),
        shading: { fill: ri % 2 === 0 ? WHITE : 'F7FBFF', type: ShadingType.CLEAR },
        margins: cellPad,
        children: [new Paragraph({
          children: [new TextRun({ text: row[ci] || '', size: 20, font: 'Arial', color: '333333' })]
        })]
      }))
    })
  );

  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: cols,
    rows: [headerRow, ...bodyRows]
  });
}

// ── Flow table ────────────────────────────────────────────────────────────────
function flowTable(content) {
  const stepW = 700;
  const descW = CONTENT_W - stepW;

  const headerRow = new TableRow({
    children: [
      new TableCell({
        width: { size: stepW, type: WidthType.DXA },
        borders: allBorders(MID_BLUE),
        shading: { fill: MID_BLUE, type: ShadingType.CLEAR },
        margins: cellPad,
        children: [new Paragraph({
          children: [new TextRun({ text: 'Step', bold: true, size: 20, color: WHITE, font: 'Arial' })]
        })]
      }),
      new TableCell({
        width: { size: descW, type: WidthType.DXA },
        borders: allBorders(MID_BLUE),
        shading: { fill: MID_BLUE, type: ShadingType.CLEAR },
        margins: cellPad,
        children: [new Paragraph({
          children: [new TextRun({ text: 'Actor  ·  Action  ·  System Response', bold: true, size: 20, color: WHITE, font: 'Arial' })]
        })]
      })
    ]
  });

  const dataRows = content.split('\n')
    .filter(l => l.trim().startsWith('|') && !l.match(/^\|[\s\-:|]+\|/))
    .slice(1)
    .map(l => l.trim().replace(/^\||\|$/g, '').split('|').map(c => c.trim()));

  const emptyRows = dataRows.length > 0 ? dataRows : Array.from({ length: 5 }, (_, i) => [`${i + 1}`, '']);
  const bodyRows = emptyRows.slice(0, 10).map((row, ri) =>
    new TableRow({
      children: [
        new TableCell({
          width: { size: stepW, type: WidthType.DXA },
          borders: allBorders(),
          shading: { fill: ri % 2 === 0 ? WHITE : 'F7FBFF', type: ShadingType.CLEAR },
          margins: cellPad,
          children: [new Paragraph({
            children: [new TextRun({ text: row[0] || `${ri + 1}`, bold: true, size: 20, font: 'Arial' })]
          })]
        }),
        new TableCell({
          width: { size: descW, type: WidthType.DXA },
          borders: allBorders(),
          shading: { fill: ri % 2 === 0 ? WHITE : 'F7FBFF', type: ShadingType.CLEAR },
          margins: cellPad,
          children: [new Paragraph({
            children: [new TextRun({ text: row[1] || '', size: 20, font: 'Arial', color: '333333' })]
          })]
        })
      ]
    })
  );

  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [stepW, descW],
    rows: [headerRow, ...bodyRows]
  });
}

// ── Desired outcomes table ────────────────────────────────────────────────────
function outcomesTable(content) {
  const cols = [5200, 2000, 2160];
  const headers = ['The system must…', 'Priority', 'AC ID'];

  const headerRow = new TableRow({
    children: headers.map((h, i) => new TableCell({
      width: { size: cols[i], type: WidthType.DXA },
      borders: allBorders(MID_BLUE),
      shading: { fill: MID_BLUE, type: ShadingType.CLEAR },
      margins: cellPad,
      children: [new Paragraph({
        children: [new TextRun({ text: h, bold: true, size: 20, color: WHITE, font: 'Arial' })]
      })]
    }))
  });

  const dataRows = content.split('\n')
    .filter(l => l.trim().startsWith('|') && !l.match(/^\|[\s\-:|]+\|/))
    .slice(1)
    .map(l => l.trim().replace(/^\||\|$/g, '').split('|').map(c => c.trim()));

  const rows = (dataRows.length > 0 ? dataRows : Array.from({ length: 5 }, () => ['', '', ''])).map((row, ri) =>
    new TableRow({
      children: cols.map((w, ci) => {
        const txt = row[ci + (row.length > 3 ? 1 : 0)] || '';
        return new TableCell({
          width: { size: w, type: WidthType.DXA },
          borders: allBorders(),
          shading: { fill: ri % 2 === 0 ? WHITE : 'F7FBFF', type: ShadingType.CLEAR },
          margins: cellPad,
          children: [new Paragraph({
            children: [new TextRun({
              text: ci === 1 ? (txt || 'Must / Should / Could') : txt,
              size: 20, font: 'Arial', color: ci === 1 ? MID_GREY : '333333',
              italics: ci === 1 && !txt
            })]
          })]
        });
      })
    })
  );

  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: cols,
    rows: [headerRow, ...rows]
  });
}

// ── Open questions table ──────────────────────────────────────────────────────
function questionsTable(content) {
  const cols = [3200, 2800, 1760, 1600];
  const headers = ['Question / Gap', 'Impact', 'Owner', 'Due Before'];

  const headerRow = new TableRow({
    children: headers.map((h, i) => new TableCell({
      width: { size: cols[i], type: WidthType.DXA },
      borders: allBorders(MID_BLUE),
      shading: { fill: MID_BLUE, type: ShadingType.CLEAR },
      margins: cellPad,
      children: [new Paragraph({
        children: [new TextRun({ text: h, bold: true, size: 20, color: WHITE, font: 'Arial' })]
      })]
    }))
  });

  const dataRows = content.split('\n')
    .filter(l => l.trim().startsWith('|') && !l.match(/^\|[\s\-:|]+\|/))
    .slice(1)
    .map(l => l.trim().replace(/^\||\|$/g, '').split('|').map(c => c.trim()));

  const rows = (dataRows.length > 0 ? dataRows : Array.from({ length: 4 }, () => ['', '', '', ''])).map((row, ri) =>
    new TableRow({
      children: cols.map((w, ci) => new TableCell({
        width: { size: w, type: WidthType.DXA },
        borders: allBorders(),
        shading: { fill: ri % 2 === 0 ? WHITE : 'FFF9F0', type: ShadingType.CLEAR },
        margins: cellPad,
        children: [new Paragraph({
          children: [new TextRun({ text: row[ci] || '', size: 20, font: 'Arial', color: '333333' })]
        })]
      }))
    })
  );

  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: cols,
    rows: [headerRow, ...rows]
  });
}

// ── Build document ────────────────────────────────────────────────────────────
const system   = extractMeta(mdText, 'System') || '';
const version  = extractMeta(mdText, 'Version') || 'v0.1 — Draft';
const author   = extractMeta(mdText, 'Author') || '';
const reviewed = extractMeta(mdText, 'Reviewed By') || '';

const purpose   = extractSection(mdText, 'Business Purpose');
const actors    = extractSection(mdText, 'Actors');
const entryExit = extractSection(mdText, 'Entry');
const coreFlow  = extractSection(mdText, 'Core Flow');
const states    = extractSection(mdText, 'States');
const outcomes  = extractSection(mdText, 'Desired Outcomes');
const oos       = extractSection(mdText, 'Out of Scope');
const questions = extractSection(mdText, 'Open Questions');

const doc = new Document({
  styles: {
    default: { document: { run: { font: 'Arial', size: 20 } } }
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 }
      }
    },
    children: [

      // ── Title ──────────────────────────────────────────────────────────────
      new Paragraph({
        spacing: { before: 0, after: 60 },
        children: [new TextRun({
          text: 'MODULE DEFINITION CARD',
          bold: true, size: 36, color: BRAND_BLUE, font: 'Arial'
        })]
      }),
      new Paragraph({
        spacing: { before: 0, after: 240 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: MID_BLUE } },
        children: [new TextRun({
          text: title, size: 26, color: MID_BLUE, font: 'Arial', bold: true
        })]
      }),
      spacer(120, 120),

      // ── Meta ───────────────────────────────────────────────────────────────
      metaTable([
        ['Module Name', title],  ['System', system],
        ['Version',     version],['Last Updated', ''],
        ['Author',      author], ['Reviewed By', reviewed],
      ]),
      spacer(240, 120),

      // ── 1. Business Purpose ───────────────────────────────────────────────
      sectionHeaderPara('1  Business Purpose'),
      spacer(80, 60),
      new Paragraph({
        spacing: { before: 0, after: 60 },
        children: [
          new TextRun({ text: 'Why does this module exist?  ', bold: true, size: 20, font: 'Arial', color: '333333' }),
          new TextRun({ text: 'What business problem does it address?', size: 20, font: 'Arial', color: MID_GREY, italics: true })
        ]
      }),
      contentPara(purpose || 'Describe in 2–3 sentences. Link to a business need, not a feature.', !purpose),
      spacer(200, 80),

      // ── 2. Actors & Roles ─────────────────────────────────────────────────
      sectionHeaderPara('2  Actors & Roles'),
      spacer(80, 80),
      contentPara('List every role that interacts with this module — front-end users and back-office operators.', true),
      actors ? actorsTable(actors) : actorsTable(''),
      spacer(200, 80),

      // ── 3. Entry & Exit Points ────────────────────────────────────────────
      sectionHeaderPara('3  Entry & Exit Points'),
      spacer(80, 80),
      ...(['Entry point', 'Pre-conditions', 'Exit point', 'Post-conditions'].map(label => {
        const re = new RegExp(`\\*\\*${label}[:\\*]+(.*?)(?=\\n\\*\\*|$)`, 'is');
        const m  = entryExit.match(re);
        return new Paragraph({
          spacing: { before: 40, after: 40 },
          children: [
            new TextRun({ text: `${label}: `, bold: true, size: 20, font: 'Arial', color: BRAND_BLUE }),
            new TextRun({ text: m ? m[1].trim() : '—', size: 20, font: 'Arial', color: '444444' })
          ]
        });
      })),
      spacer(200, 80),

      // ── 4. Core Flow ──────────────────────────────────────────────────────
      sectionHeaderPara('4  Core Flow'),
      spacer(80, 80),
      contentPara('Each step: Actor → Action → System response. Max 10 steps.', true),
      coreFlow ? flowTable(coreFlow) : flowTable(''),
      spacer(200, 80),

      // ── 5. States & Edge Cases ────────────────────────────────────────────
      sectionHeaderPara('5  States & Edge Cases'),
      spacer(80, 80),
      contentPara(states || '—', !states),
      spacer(200, 80),

      // ── 6. Desired Outcomes ───────────────────────────────────────────────
      sectionHeaderPara('6  Desired Outcomes  →  Acceptance Criteria Seeds'),
      spacer(80, 80),
      contentPara('"The system must…" — these become AC entries in the companion workbook.', true),
      outcomes ? outcomesTable(outcomes) : outcomesTable(''),
      spacer(200, 80),

      // ── 7. Out of Scope ───────────────────────────────────────────────────
      sectionHeaderPara('7  Out of Scope'),
      spacer(80, 80),
      contentPara(oos || 'List what this module explicitly does NOT handle.', !oos),
      spacer(200, 80),

      // ── 8. Open Questions ─────────────────────────────────────────────────
      sectionHeaderPara('8  Open Questions & Flags'),
      spacer(80, 80),
      questions ? questionsTable(questions) : questionsTable(''),
      spacer(280, 80),

      // ── Footer ────────────────────────────────────────────────────────────
      new Paragraph({
        spacing: { before: 200, after: 0 },
        border: { top: { style: BorderStyle.SINGLE, size: 4, color: MID_BLUE } },
        children: [
          new TextRun({
            text: 'Data Dictionary and Acceptance Criteria are maintained in the companion module-workbook.xlsx  ·  ',
            size: 16, color: MID_GREY, font: 'Arial', italics: true
          }),
          new TextRun({
            text: 'This card is the source of truth for scope and flow.',
            size: 16, color: MID_GREY, font: 'Arial', italics: true, bold: true
          })
        ]
      })
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(outPath, buffer);
  console.log(`  ✅  ${path.basename(outPath)}  →  ${outPath}`);
}).catch(err => {
  console.error('Error generating docx:', err.message);
  process.exit(1);
});
