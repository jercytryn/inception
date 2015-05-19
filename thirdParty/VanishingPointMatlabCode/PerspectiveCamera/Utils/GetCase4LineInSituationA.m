function hypSelectLines = GetCase4LineInSituationA(id, num1, num2)
%function to generate a hypothesis including indices of four lines
%Input:   id  -- the hypothesis id in all possible combinations in situationA,
%         num1-- the number of lines in the first part of situationA
%         num2-- the number of lines in the second part of situationA
%Output:  hypSelectLines = [lineId1, lineId2, lineId3, lineId4]
%         lineId1, lineId2 are ids in the fisrt part of situationA;
%         lineId3, lineId4 are ids in the second part of situationA;

%The id should smaller than the largest number of possible combinations,
%which equals to num1*(num1-1)*num2*(num2-1)/4 (i.e. two lines from part1 and two lines from part2).  
%E.g.: GetCase4LineInSituationA(1, 3, 3) = [2,1,2,1]
%      GetCase4LineInSituationA(2, 3, 3) = [2,1,3,1]
%      GetCase4LineInSituationA(3, 3, 3) = [2,1,3,2]
%      GetCase4LineInSituationA(4, 3, 3) = [3,1,2,1]
%      GetCase4LineInSituationA(5, 3, 3) = [3,1,3,1]
%      GetCase4LineInSituationA(6, 3, 3) = [3,1,3,2]
%      GetCase4LineInSituationA(7, 3, 3) = [3,2,2,1]
%      GetCase4LineInSituationA(8, 3, 3) = [3,2,3,1]
%      GetCase4LineInSituationA(9, 3, 3) = [3,2,3,2]
kEqualityTo0 =  1e-12;
maxId1 = num1*(num1-1)/2;
maxId2 = num2*(num2-1)/2;

if id > maxId1*maxId2
    error('the index is larger than the largest number of possible combinations');
end

%(id1-1)*maxId2 + id2 = id;
id1 = ceil(id/maxId2);
id2 = id - (id1-1)*maxId2;

%solve nchoosek(lineId1,2) = id1 can get an estimate of lineId1;
lineId1 = 0.5*(1 + sqrt(1+8*id1));
if abs(lineId1 - round(lineId1)) < kEqualityTo0
    lineId1 = round(lineId1);
    lineId2 = lineId1 - 1;
else
    lineId1 = floor(lineId1)+1;
    lineId2 = id1 - (lineId1-1)*(lineId1-2)/2;
end

%solve nchoosek(lineId3,2) = id2 can get an estimate of lineId3;
lineId3 = 0.5*(1 + sqrt(1+8*id2));
if abs(lineId3 - round(lineId3)) < kEqualityTo0
    lineId3 = round(lineId3);
    lineId4 = lineId3 - 1;
else
    lineId3 = floor(lineId3)+1;
    lineId4 = id2 - (lineId3-1)*(lineId3-2)/2;
end

hypSelectLines = [lineId1, lineId2, lineId3, lineId4];


