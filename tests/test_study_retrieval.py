"""Check source citation, safe suggestions, and local-upload boundaries."""
from io import BytesIO
import unittest
from study_retrieval import StudyIndex, chunks_for_pages, suggestions, MAX_FILE_BYTES


class StudyRetrievalTests(unittest.TestCase):
    def test_search_preserves_page_and_requires_matching_terms(self):
        index=StudyIndex()
        index.add('paper.txt',b'Serpent venom study. PLA2: 24.5% and SVMP 10%.')
        hits=index.search('venom PLA2')
        self.assertEqual(len(hits),1)
        self.assertEqual(hits[0]['study'],'paper.txt')
        self.assertEqual(hits[0]['page'],1)
        self.assertEqual([(x['component'],x['value']) for x in hits[0]['suggestions']], [('pla2',24.5),('svmp',10)])
        self.assertEqual(index.search('no-matching-term'),[])
        self.assertEqual(len(hits[0]['sha256']),64)

    def test_percentage_extraction_is_narrow_and_rejects_ranges(self):
        actual=suggestions('3FTx: 30%; PLA2 10–20%; BPP -5%; CLP 8%; SVMP 120%; SVSP (2.5%).')
        self.assertEqual([(x['component'],x['value']) for x in actual],[('3ftx',30),('svsp',2.5)])

    def test_upload_limits_duplicates_and_clear(self):
        index=StudyIndex()
        with self.assertRaisesRegex(ValueError,'PDF or UTF-8'): index.add('paper.html',b'x')
        with self.assertRaisesRegex(ValueError,'not a PDF'): index.add('paper.pdf',b'bad')
        with self.assertRaisesRegex(ValueError,'No extractable'): index.add('paper.txt',b'  \n')
        with self.assertRaisesRegex(ValueError,'12 MB'): index.add('huge.txt',b'x'*(MAX_FILE_BYTES+1))
        first=index.add('../first.txt',b'Venom PLA2: 3%.')
        self.assertEqual(first['name'],'first.txt')
        self.assertTrue(index.add('duplicate.txt',b'Venom PLA2: 3%.')['duplicate'])
        for i in range(4): index.add(f'p{i}.txt',f'study {i}'.encode())
        with self.assertRaisesRegex(ValueError,'five'):index.add('one-more.txt',b'another')
        index.clear();self.assertEqual(index.search('venom'),[])

    def test_chunks_do_not_infer_values_across_page_boundaries(self):
        chunks=chunks_for_pages(['PLA2:', '5%'])
        self.assertEqual([c['page'] for c in chunks],[1,2])
        self.assertFalse(any(suggestions(c['text']) for c in chunks))

    def test_real_text_pdf_page_number(self):
        try:
            from reportlab.pdfgen import canvas
            import pypdf
        except ImportError:
            self.skipTest('PDF libraries unavailable in this interpreter')
        output=BytesIO();pdf=canvas.Canvas(output);pdf.drawString(50,750,'Introductory page');pdf.showPage()
        pdf.drawString(50,750,'Viper sample SVMP: 44.2%');pdf.save()
        index=StudyIndex();index.add('study.pdf',output.getvalue())
        hit=index.search('SVMP')[0]
        self.assertEqual(hit['page'],2)
        self.assertEqual(hit['suggestions'][0]['value'],44.2)

if __name__=='__main__':unittest.main()
