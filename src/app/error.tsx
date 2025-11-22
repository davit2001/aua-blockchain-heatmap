"use client";

import SomethingWentWrongIcon from "@/assets/something-went-wrong.svg";

const ErrorPage = () => (
    <div className="px-4 mx-auto w-full h-screen justify-center max-w-container flex flex-col items-center desktop:gap-10 tablet:gap-8 mobile:gap-[60px]">
        <SomethingWentWrongIcon className="w-full h-auto"/>
        <div className="flex flex-col tablet:gap-6 mobile:gap-4">
            <h1 className="desktop:text-[56px] tablet:text-[40px] mobile:text-[32px] text-primary text-center font-bold">
                Opps! Something Went Wrong
            </h1>
            <p className="text-center text-tertiary desktop:text-2xl tablet:text-xl mobile:text-sm">
                We are sorry, but an unexpected error occurred. Please try refreshing the page or come back later. If the issue persists
            </p>
        </div>
    </div>
);

export default ErrorPage;
