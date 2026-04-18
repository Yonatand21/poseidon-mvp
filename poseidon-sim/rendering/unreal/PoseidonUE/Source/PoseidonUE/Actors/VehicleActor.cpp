#include "Actors/VehicleActor.h"

#include "Bridge/PoseidonBridge.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"

AVehicleActor::AVehicleActor()
{
    PrimaryActorTick.bCanEverTick = true;
    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    RootComponent = SceneRoot;
}

void AVehicleActor::BeginPlay()
{
    Super::BeginPlay();

    if (UGameInstance* GI = UGameplayStatics::GetGameInstance(this))
    {
        Bridge = GI->GetSubsystem<UPoseidonBridge>();
    }

    if (Bridge && !TopicName.IsEmpty())
    {
        Bridge->OnMessage.AddDynamic(this, &AVehicleActor::HandleBridgeMessage);
        Bridge->Subscribe(TopicName, MessageType);
    }
}

void AVehicleActor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);

    if (!bHasSample)
    {
        return;
    }

    // Simple critically-damped lerp so the actor does not snap.
    const float Alpha = FMath::Clamp(DeltaSeconds * 10.0f, 0.0f, 1.0f);
    SetActorLocation(FMath::Lerp(GetActorLocation(), TargetLocation, Alpha));
    SetActorRotation(FQuat::Slerp(GetActorQuat(), TargetOrientation, Alpha));
}

static bool ExtractTopicName(const TSharedPtr<FJsonObject>& Root, FString& Out)
{
    return Root.IsValid() && Root->TryGetStringField(TEXT("topic"), Out);
}

void AVehicleActor::HandleBridgeMessage(const FString& JsonPayload)
{
    TSharedPtr<FJsonObject> Root;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonPayload);
    if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
    {
        return;
    }

    FString IncomingTopic;
    if (!ExtractTopicName(Root, IncomingTopic) || IncomingTopic != TopicName)
    {
        return;
    }

    const TSharedPtr<FJsonObject>* Msg = nullptr;
    if (!Root->TryGetObjectField(TEXT("msg"), Msg) || !Msg)
    {
        return;
    }

    const TSharedPtr<FJsonObject>* Pose = nullptr;
    const TSharedPtr<FJsonObject>* Inner = nullptr;
    if (!(*Msg)->TryGetObjectField(TEXT("pose"), Pose) || !Pose) { return; }
    if (!(*Pose)->TryGetObjectField(TEXT("pose"), Inner) || !Inner) { return; }

    const TSharedPtr<FJsonObject>* Position = nullptr;
    const TSharedPtr<FJsonObject>* Orientation = nullptr;
    if (!(*Inner)->TryGetObjectField(TEXT("position"), Position) || !Position) { return; }
    if (!(*Inner)->TryGetObjectField(TEXT("orientation"), Orientation) || !Orientation) { return; }

    const double Px = (*Position)->GetNumberField(TEXT("x"));
    const double Py = (*Position)->GetNumberField(TEXT("y"));
    const double Pz = (*Position)->GetNumberField(TEXT("z"));

    const double Qx = (*Orientation)->GetNumberField(TEXT("x"));
    const double Qy = (*Orientation)->GetNumberField(TEXT("y"));
    const double Qz = (*Orientation)->GetNumberField(TEXT("z"));
    const double Qw = (*Orientation)->GetNumberField(TEXT("w"));

    // ENU (ROS) -> UE5 left-handed: x->x, y->-y, z->z, flip yaw.
    TargetLocation = FVector(Px * WorldScale, -Py * WorldScale, Pz * WorldScale);
    TargetOrientation = FQuat(Qx, -Qy, Qz, -Qw);
    bHasSample = true;
}
