"""A local answer must use retrieved text and never apply values."""
import io
import json
import unittest
from study_answer import answer, OLLAMA_URL, NoRedirect
from study_retrieval import StudyIndex


class StudyAnswerTests(unittest.TestCase):
    def setUp(self):
        self.index=StudyIndex();self.index.add('paper.txt',b'Venom sample: PLA2: 25%.')

    def test_grounded_answer_supplies_cited_sources_to_fixed_local_endpoint(self):
        calls=[]
        def opener(request,timeout):
            calls.append((request,timeout));return io.BytesIO(json.dumps({'response':'The sample contained PLA2 [1].'}).encode())
        result=answer(self.index,'What was PLA2?',opener)
        req,_=calls[0];self.assertEqual(req.full_url,OLLAMA_URL)
        payload=json.loads(req.data);self.assertIn('PLA2: 25%',payload['prompt']);self.assertFalse(payload['stream'])
        self.assertTrue(result['citations_well_formed']);self.assertEqual(result['sources'][0]['page'],1)
        self.assertNotIn('suggestions',result)

    def test_invalid_citations_are_flagged_and_no_context_is_refused(self):
        def opener(request,timeout): return io.BytesIO(b'{"response":"Not a supported citation [8]."}')
        self.assertFalse(answer(self.index,'PLA2',opener)['citations_well_formed'])
        with self.assertRaisesRegex(ValueError,'No matching'):answer(self.index,'no-unrelated-terms',opener)
        self.assertIsNone(NoRedirect().redirect_request(None,None,302,None,None,'https://example.com'))

if __name__=='__main__':unittest.main()
