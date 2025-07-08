# Runpy

파이썬 함수를 cli cmd로 자동 변환해주는 library를 구현할 것임.

Args:
    name: description

뭐 저런 식으로 적혀있으면, fastapi같은 것에서 알아서 arg의 description parsing할 수 있던가?

그럼 fastapi의 schema 생성기능을 적극 활용하면 될 것 같음.


생성기 class가 있을건데,

함수를 하나씩 등록하는 식으로 cmd를 완성함.

우리는 아무 함수나도 cli로 변환하고 쉽기 때문에, docstring상 더 장난은 치진 않고,

cmd를 생성할 때, {"name": "n", "version": "v"} ... 저런 식으로 숏컷은 자동생성 등록할 때 정할 수 있으면 좋겠음.

그리고 instance가 생성될 때 cmd 경로같은 것도 받을건데,

mycli/mycmd/subcmd

위와같은 식이라하면,

mycli mycmd subcmd --name John ...

와 같이 쓸 수 있는 식.

더 깊게도 가능.

그래서 여러 구조로 생성가능.


모듈을 단순화 하기 위해, 굳이 arguments나 flags등을 받지 않을 것임. 모두가 옵션.

흠... 

def func(a: int, b: int, *args: int, c: int):
    pass

그럼 저런 *를 처리 못 하게 되니, 그냥 두는게 나을 듯. 놔두고 *가 있으면 arg로 처리.

그리고 모든 cmd는(한 클라스가 생성한)는 schema라는 명령어도 가질거임.

이 schema는 api schema의 형태로, cli 사용법을 설명해 줄 것임.

기존에는 cleo를 써서 구현했었는데,

sub command 구현문제때문에 click으로 구현해야할 것 같음.

## 참고

cli-bridge가 초기 형태이고,
func-analyzer는 함수로부터 이에 필요한 정보를 뽑아내기 위해 개발했는데,
fastapi의 기능을 써서 충분하다면, 안써도 됨.

