from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import matplotlib.pyplot as plt

def evaluer(y_true, y_pred, classes):
    acc = accuracy_score(y_true, y_pred)
    print(f"Accuracy : {acc:.1%}\n")
    print(classification_report(y_true, y_pred, labels=classes, zero_division=0))

    cm = confusion_matrix(y_true, y_pred, labels=classes)
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(classes)))
    ax.set_yticks(range(len(classes)))
    ax.set_xticklabels(classes, rotation=45, ha="right")
    ax.set_yticklabels(classes)
    ax.set_xlabel("Prédit par le modèle")
    ax.set_ylabel("Vraie classe")
    for i in range(len(classes)):
        for j in range(len(classes)):
            ax.text(j, i, cm[i, j], ha="center", va="center")
    plt.tight_layout()
    plt.show()
    return acc, cm

if __name__ == "__main__":
    import random
    from predict import CLASSES
    y_true = [random.choice(CLASSES) for _ in range(100)]
    y_pred = [random.choice(CLASSES) for _ in range(100)]
    evaluer(y_true, y_pred, CLASSES)