import sys

from crossword import Crossword, Variable
from collections import deque

class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        # Removes all values in v
        for v in self.domains:
            v_copy = self.domains[v].copy()
            for x in self.domains[v]:
                if len(x) != v.length:
                    v_copy.remove(x)
            self.domains[v] = v_copy

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        overlap = self.crossword.overlaps[(x,y)]
        # If no overlap, change nothing
        if overlap is None:
            return False
        
        # index of word x and index of word y
        i,j = overlap

        removed = False
        to_remove = set()

        for word_x in self.domains[x]:
            supported = False
            for word_y in self.domains[y]:
                # There exists a value in the word x and y that overlap at the correct point
                if word_x[i] == word_y[j]:
                    supported = True
                    break
            # If it doesnt exist, remove the word from domain x
            if not supported:
                to_remove.add(word_x)

        # remove done at end to avoid iterating errors
        if to_remove:
            self.domains[x] = self.domains[x] - to_remove
            removed = True

        return removed


    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        # if arcs is none, create a queue containing all variable (x,y) overlaps
        if arcs is None:
            queue = deque()
            for x in self.crossword.variables:
                for y in self.crossword.neighbors(x):
                    if self.crossword.overlaps[(x, y)] is not None:
                        queue.append((x,y))
        # else create a queue with all arcs listed
        else:
            queue = deque(arcs)

        # revise each (x,y) pair in the queue
        while queue:
            x, y = queue.popleft()
            if self.revise(x,y):
                # return false if domain becomes empty
                if not self.domains[x]:
                    return False
                # remove y from x's neighbours set and add them to the queue again
                for z in self.crossword.neighbors(x) - {y}:
                    if self.crossword.overlaps[(z,x)] is not None:
                        queue.append((z, x))

        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for var in self.crossword.variables:
            if var not in assignment or assignment[var] is None:
                return False
            
        return True

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        # check if all different
        values = list(assignment.values())
        if len(values) != len(set(values)):
            return False
        
        # check length
        for var, word in assignment.items():
            if len(word) != var.length:
                return False
            
        # Check each assigned word fits correctly with neighbours at overlap points
        for x, xword in assignment.items():
            for y in self.crossword.neighbors(x):
                if y in assignment:
                    overlap = self.crossword.overlaps[(x,y)]
                    if overlap is None:
                        continue
                    i, j = overlap
                    if xword[i] != assignment[y][j]:
                        return False
                    
        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        # Least contraining values (LCV) heuristic
        scores = {} # how many neighbour values it would eliminate

        for word in self.domains[var]:
            count = 0
            for nbr in self.crossword.neighbors(var):
                # goto next neighbour if neighbour already has an assigned value
                if nbr in assignment:
                    continue
                overlap = self.crossword.overlaps[(var, nbr)]
                if overlap is None:
                    continue
                i, j = overlap
                # count neighbour words that would be incompatile
                for nbr_word in self.domains[nbr]:
                    if word[i] != nbr_word[j]:
                        count += 1
            scores[word] = count

        # returns a sorted list of words based on thier score in ascending order
        return sorted(self.domains[var], key=lambda w: scores[w])

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        # create a list of unassigned variables
        unassigned = [v for v in self.crossword.variables if v not in assignment]

        # Build (domain_size, -degree, var) tuples for sorting (MRV, degree heuristc)
        ranked = []
        for var in unassigned:
            domain_size = len(self.domains[var])
            degree = len(self.crossword.neighbors(var))
            ranked.append((domain_size, -degree, var))

        # sort by domain size asc then degree desc
        ranked.sort(key=lambda x: (x[0], x[1]))

        # return best variable
        return ranked[0][2]

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        # Time and calls calculation for diagnostics
        import time
        if not hasattr(self, 'backtrack_start'):
            self.backtrack_start = time.time()
            self.backtrack_calls = 0

        self.backtrack_calls += 1

        # Backtrack function
        if self.assignment_complete(assignment):
            total_time = time.time() - self.backtrack_start
            print(f"Backtrack Time taken: {total_time:.6f}s")
            print(f"Bactrack calls {self.backtrack_calls}")
            return assignment
        
        # choose smallest domain size variable with highest degree
        var = self.select_unassigned_variable(assignment)
        # choose word in domain that would eliminate minimum neighbour values
        ordered_domain = self.order_domain_values(var, assignment)
        for w in ordered_domain:
            # add this word to assignment[var] and check if consistent, remove if not 
            # run until all variables have been assigned
            assignment[var] = w
            if self.consistent(assignment):
                result = self.backtrack(assignment)
                if result is not None:
                    return result
            del assignment[var]
        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()

# python3 generate.py data/structure0.txt data/words0.txt out0.png
