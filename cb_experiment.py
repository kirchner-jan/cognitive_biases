from torch.utils.data import Dataset
from abc import ABCMeta, abstractmethod
from query_api import get_completion
import re , pickle
from typing import List

class CognitiveBiasExperiment(Dataset, metaclass=ABCMeta):
    """
    Cognitive Biases dataset.
    """
    pass
    def __init__(self , name , length) -> None:
        self.name = name
        self.length = length
        self.context = 'This is the transcript of a conversation between a researcher and a subject who agreed to answer a few questions honestly and to the best of their ability.\n---BEGIN TRANSCRIPT---\n'
        self.template = ''
    def ___len___(self) -> int:
       return self.length

    @abstractmethod
    def __getitem__(self, index) -> None:
       pass


# class HaloEffect(CognitiveBiasExperiment):
#     def __init__(self, name , length) -> None:
#         super().__init__(name , length)
#     def __getitem__(self, index) -> None:
#         return super().__getitem__(index)

class ConjunctionFallacy(CognitiveBiasExperiment):
    """
    Dataset of the conjunction fallacy. Uses GPT-neox to procedurally generate examples.
    """
    def __init__(self, filepath = None) -> None:
        """
        Initializes from file or empty.
        """
        super().__init__('conjunction fallacy', 1)
        self.number_regex = r'^[-+]?[0-9]+\.'
        self.length = None
        self.template_path = './templates/conjunction_fallacy_template.txt'

        with open(self.template_path) as f:
            self.template = f.readlines()[0]
        
        if filepath is not None:
            self.init_from_file(self,filepath)
        else:
            self.building_blocks = {}

    def init_from_file(self,filepath):
        """
        Load previously generated building blocks from a provided file path.
        """
        with open(filepath , "rb") as f:
            load_dict = pickle.load(f)
        self.building_blocks = load_dict
    
    def save_to_file(self,filepath):
        """
        Saves generated building blocks to a provided file path.
        """
        with open(filepath , "wb") as f:
            pickle.dump(self.building_blocks , f)

    def generate(self , query , process1 , process2 , regex_pattern , min_length=4 , max_tokens=50) -> List[str]:
        """
        Generates a list of suggestions.
        """
        print(query)
        rejected = True
        while rejected:
            suggestions = get_completion(query , stream_flag=False , max_tokens=max_tokens)
            suggestions = process1(suggestions)
            suggestions = [process2(name) for name in suggestions
                                if re.match(regex_pattern, name) and len(process2(name)) >= min_length]
            print(', '.join(suggestions))
            rejected = (input('resample? (y/n) ') == 'y')
        return suggestions

    def generate_name(self) -> None:
        """
        Generates possible names for the experiment.
        """
        self.building_blocks['names'] = self.generate('Here is a list of popular Western names:\n1. Linda\n2. Daniel\n3. ' ,
                                               lambda x : x.choices[0].text.split('\n'),
                                               lambda x : x.split('.')[1][1:],
                                               self.number_regex)

    def generate_occupation(self) -> None:
        """
        Generates possible occupations for the experiment.
        """
        self.building_blocks['occupations'] = self.generate('Here is a list of common occupations:\n1. Banker\n2. Teacher\n3. ' ,
                                               lambda x : x.choices[0].text.split('\n'),
                                               lambda x : x.split('.')[1][1:].lower(),
                                               self.number_regex)

    def generate_hobbies(self) -> None:
        """
        Generates possible unlikely hobbies for the experiment.
        """
        if 'occupations' not in self.building_blocks:
            print('Need to generate occupations first.')
            self.generate_occupation()
        hobbies = []
        for occupation in self.building_blocks['occupations']:
            hobbies +=  [self.generate('Here is a list of unlikely pairing of jobs and hobbies:\n1. a bank teller but active in the feminist movement\n2. a {atypical} but'.format(atypical=occupation) ,
                                               lambda x : x.choices[0].text.split('\n'),
                                                lambda x : x[1:].lower(),
                                                r'.*')[0]]
        self.building_blocks['hobbies'] = hobbies

    def generate_description(self) -> None:
        if 'hobbies' not in self.building_blocks:
            print('Need to generate hobbies first.')
            self.generate_hobbies()
        descriptions = []
        for hobby in self.building_blocks['hobbies']:
            descriptions += [self.generate('Here is a list of descriptions of people with certain hobbies:\n1. Someone who is active in the feminist movement might be 31 years old, single, outspoken, and very bright. They majored in philosophy. As a student, they were deeply concerned with issues of discrimination and social justice, and also participated in anti-nuclear demonstrations.\n2. Someone who {hobby} might be'.format(hobby=hobby) ,
                                               lambda x : x.choices[0].text.split('\n'),
                                                lambda x : x[1:],
                                                r'.*', max_tokens=150)[0]]
        self.building_blocks['descriptions'] = descriptions

    def __getitem__(self, index) -> str:
       return str(index)