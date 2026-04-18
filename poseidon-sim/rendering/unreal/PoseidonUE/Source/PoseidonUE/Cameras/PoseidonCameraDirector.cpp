#include "Cameras/PoseidonCameraDirector.h"

#include "Bridge/PoseidonBridge.h"
#include "Camera/CameraComponent.h"
#include "Camera/CameraActor.h"
#include "Components/InputComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

static const FName TAG_AUV = TEXT("PoseidonAUV");
static const FName TAG_SSV = TEXT("PoseidonSSV");

APoseidonCameraDirector::APoseidonCameraDirector()
{
    PrimaryActorTick.bCanEverTick = true;
    USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    RootComponent = Root;

    ChaseCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("ChaseCamera"));
    ChaseCamera->SetupAttachment(Root);
    ChaseCamera->FieldOfView = 90.f;

    TopDownCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("TopDownCamera"));
    TopDownCamera->SetupAttachment(Root);
    TopDownCamera->SetProjectionMode(ECameraProjectionMode::Orthographic);
    TopDownCamera->OrthoWidth = 80000.f;  // ~800 m field width

    DropCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("DropCamera"));
    DropCamera->SetupAttachment(Root);
    DropCamera->FieldOfView = 60.f;
}

void APoseidonCameraDirector::BeginPlay()
{
    Super::BeginPlay();

    PC = UGameplayStatics::GetPlayerController(this, 0);

    for (TActorIterator<AActor> It(GetWorld()); It; ++It)
    {
        if (It->ActorHasTag(TAG_AUV)) { AuvActor = *It; }
        if (It->ActorHasTag(TAG_SSV)) { SsvActor = *It; }
    }

    if (UGameInstance* GI = UGameplayStatics::GetGameInstance(this))
    {
        if (UPoseidonBridge* Bridge = GI->GetSubsystem<UPoseidonBridge>())
        {
            Bridge->OnMessage.AddDynamic(this, &APoseidonCameraDirector::HandleBridgeMessage);
            Bridge->Subscribe(TEXT("/coupling/drop_cmd"), TEXT("std_msgs/Empty"));
        }
    }

    BindInputActions();
    SetPreset(EPoseidonCameraPreset::Chase);
}

void APoseidonCameraDirector::BindInputActions()
{
    EnableInput(PC);
    if (InputComponent == nullptr)
    {
        return;
    }

    InputComponent->BindAction("CameraChase",         IE_Pressed, this, &APoseidonCameraDirector::ActivateChase);
    InputComponent->BindAction("CameraTopDown",       IE_Pressed, this, &APoseidonCameraDirector::ActivateTopDown);
    InputComponent->BindAction("CameraDropCinematic", IE_Pressed, this, &APoseidonCameraDirector::ActivateDropCinematic);
}

void APoseidonCameraDirector::SetPreset(EPoseidonCameraPreset NewPreset)
{
    CurrentPreset = NewPreset;

    if (!PC)
    {
        return;
    }

    UCameraComponent* Selected = nullptr;
    switch (NewPreset)
    {
        case EPoseidonCameraPreset::Chase:         Selected = ChaseCamera;   break;
        case EPoseidonCameraPreset::TopDown:       Selected = TopDownCamera; break;
        case EPoseidonCameraPreset::DropCinematic: Selected = DropCamera;    break;
    }
    if (Selected)
    {
        PC->SetViewTarget(this);
        if (NewPreset == EPoseidonCameraPreset::DropCinematic)
        {
            DropElapsedSeconds = 0.f;
            DropAnchor = AuvActor ? AuvActor->GetActorLocation() : GetActorLocation();
        }
    }
}

void APoseidonCameraDirector::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    switch (CurrentPreset)
    {
        case EPoseidonCameraPreset::Chase:         UpdateChase(DeltaSeconds); break;
        case EPoseidonCameraPreset::TopDown:       UpdateTopDown(DeltaSeconds); break;
        case EPoseidonCameraPreset::DropCinematic: UpdateDropCinematic(DeltaSeconds); break;
    }
}

void APoseidonCameraDirector::UpdateChase(float DeltaSeconds)
{
    if (!AuvActor || !ChaseCamera) { return; }
    const FVector Target = AuvActor->GetActorLocation();
    const FRotator Yaw(0.f, AuvActor->GetActorRotation().Yaw, 0.f);
    const FVector Desired = Target + Yaw.RotateVector(ChaseOffsetMeters * WorldScale);
    const FVector Smoothed = FMath::VInterpTo(ChaseCamera->GetComponentLocation(), Desired, DeltaSeconds, 4.f);
    ChaseCamera->SetWorldLocation(Smoothed);
    const FRotator LookAt = (Target - Smoothed).Rotation();
    ChaseCamera->SetWorldRotation(LookAt);
}

void APoseidonCameraDirector::UpdateTopDown(float DeltaSeconds)
{
    if (!TopDownCamera) { return; }
    FVector Mid = FVector::ZeroVector;
    int32 Count = 0;
    if (AuvActor) { Mid += AuvActor->GetActorLocation(); ++Count; }
    if (SsvActor) { Mid += SsvActor->GetActorLocation(); ++Count; }
    if (Count > 0) { Mid /= Count; }
    Mid.Z = TopDownAltitudeMeters * WorldScale;
    TopDownCamera->SetWorldLocation(Mid);
    TopDownCamera->SetWorldRotation(FRotator(-90.f, 0.f, 0.f));
}

void APoseidonCameraDirector::UpdateDropCinematic(float DeltaSeconds)
{
    if (!DropCamera) { return; }
    DropElapsedSeconds += DeltaSeconds;
    const float T = FMath::Clamp(DropElapsedSeconds / DropCinematicDurationSeconds, 0.f, 1.f);
    const float Ease = 1.f - FMath::Pow(1.f - T, 3.f);
    const FVector StartOffset = FVector(-2500.f, 2500.f, 1500.f);
    const FVector EndOffset   = FVector(-400.f,  200.f,  200.f);
    const FVector Pos = DropAnchor + FMath::Lerp(StartOffset, EndOffset, Ease);
    DropCamera->SetWorldLocation(Pos);
    DropCamera->SetWorldRotation((DropAnchor - Pos).Rotation());

    if (T >= 1.f)
    {
        SetPreset(EPoseidonCameraPreset::Chase);
    }
}

void APoseidonCameraDirector::HandleBridgeMessage(const FString& JsonPayload)
{
    TSharedPtr<FJsonObject> Root;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonPayload);
    if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid()) { return; }

    FString Topic;
    if (!Root->TryGetStringField(TEXT("topic"), Topic)) { return; }
    if (Topic == TEXT("/coupling/drop_cmd"))
    {
        SetPreset(EPoseidonCameraPreset::DropCinematic);
    }
}
